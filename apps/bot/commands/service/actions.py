from apps.bot.classes.command import Command
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Chat
from petrovich.settings import env


class Actions(Command):
    names = None
    priority = 100

    def accept(self, event: Event) -> bool:
        return bool(event.action)

    def start(self) -> ResponseMessage:
        new_chat_members = self.event.action.get('new_chat_members')
        left_chat_member = self.event.action.get('left_chat_member')
        migrate_from_chat_id = self.event.action.get('migrate_from_chat_id')
        group_chat_created = self.event.action.get('group_chat_created')
        if new_chat_members:
            answer = []
            for member in new_chat_members:
                answer.append(self.setup_new_chat_member(member['id'], is_bot=member['is_bot']))
            answer = answer[0]
            if answer:
                return ResponseMessage(ResponseMessageItem(text=answer))
        elif left_chat_member:
            self.setup_left_chat_member(left_chat_member['id'], is_bot=left_chat_member['is_bot'])
        elif migrate_from_chat_id:
            self.setup_new_chat_id(migrate_from_chat_id)
        elif group_chat_created:
            answer = self.group_chat_created()
            return ResponseMessage(ResponseMessageItem(text=answer))

    def setup_new_chat_member(self, member_id, is_bot):
        if not is_bot:
            profile = self.bot.get_profile_by_user_id(member_id)
            self.bot.add_chat_to_profile(profile, self.event.chat)
        else:
            bot_group_id = env.int('TG_BOT_GROUP_ID')
            if member_id != bot_group_id:
                return

            if self.event.chat.admin is None:
                return self.group_chat_created()
            else:
                return "Давненько не виделись!"

    def setup_left_chat_member(self, member_id, is_bot):
        if not is_bot:
            profile = self.bot.get_profile_by_user_id(member_id)
            self.bot.remove_chat_from_profile(profile, self.event.chat)

    def setup_new_chat_id(self, chat_id):
        chat = Chat.objects.get(chat_id=chat_id)
        chat.chat_id = self.event.chat.chat_id
        chat.save()
        self.event.chat.delete()

    def group_chat_created(self):
        self.event.chat.admin = self.event.sender
        self.event.chat.save()
        return f"Администратором конфы является {self.event.sender}\n" \
               f"Задайте имя конфы:\n" \
               "/конфа {Название конфы}"

    # По изменению чата конфы
    # elif self.event.action['type'] == 'chat_title_update':
    #     self.event.chat.name = self.event.action['text']
    #     self.event.chat.save()
