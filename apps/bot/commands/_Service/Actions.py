from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PError
from apps.bot.models import Chat
from apps.games.models import PetrovichUser
from apps.service.models import Tag
from petrovich.settings import env


class Actions(Command):
    names = None
    priority = 100

    def accept(self, event):
        return bool(event.action)

    def start(self):
        new_chat_members = self.event.action.get('new_chat_members')
        left_chat_member = self.event.action.get('left_chat_member')
        migrate_from_chat_id = self.event.action.get('migrate_from_chat_id')
        if new_chat_members:
            answer = []
            for member in new_chat_members:
                answer.append(self.setup_new_chat_member(member['id'], is_bot=member['is_bot']))
            return answer[0]
        elif left_chat_member:
            for member in left_chat_member:
                self.setup_left_chat_member(member['id'], is_bot=member['is_bot'])
        elif migrate_from_chat_id:
            self.setup_new_chat_id(migrate_from_chat_id)

    def setup_new_chat_member(self, member_id, is_bot):
        if not is_bot:
            profile = self.bot.get_profile_by_user_id(member_id)
            self.bot.add_chat_to_profile(profile, self.event.chat)
        else:
            if self.event.platform == Platform.VK:
                bot_group_id = env.int('VK_BOT_GROUP_ID')
            elif self.event.platform == Platform.TG:
                bot_group_id = env.int('TG_BOT_GROUP_ID')
            else:
                raise PError("Неизвестный клиент")

            if member_id == bot_group_id:
                if self.event.chat.admin is None:
                    self.event.chat.admin = self.event.sender
                    self.event.chat.save()
                    return f"Администратором конфы является {self.event.sender}\n" \
                           f"Задайте имя конфы:\n" \
                           "/конфа {Название конфы}"
                else:
                    return "Давненько не виделись!"
            else:
                self.bot.get_bot_by_id(member_id)

    def setup_left_chat_member(self, member_id, is_bot):
        if not is_bot:
            profile = self.bot.get_profile_by_user_id(member_id)
            self.bot.remove_chat_from_profile(profile, self.event.chat)

            # Tags
            tags_with_user = Tag.objects.filter(chat=self.event.chat, users__in=[profile])
            for tag in tags_with_user:
                tag.users.remove(profile)

            # Petrovich Game
            pu = PetrovichUser.objects.filter(chat=self.event.chat, profile=profile)
            if pu.exists():
                pu.active = False
                pu.save()

    def setup_new_chat_id(self, chat_id):
        chat = Chat.objects.get(chat_id=chat_id)
        chat.chat_id = self.event.chat.chat_id
        chat.save()
        self.event.chat.delete()

    # По изменению чата конфы
    # elif self.event.action['type'] == 'chat_title_update':
    #     self.event.chat.name = self.event.action['text']
    #     self.event.chat.save()
