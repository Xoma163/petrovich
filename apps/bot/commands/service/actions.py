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
        new_chat_title = self.event.action.get('new_chat_title')

        answer = None
        if new_chat_members:
            answers = [self.setup_new_chat_member(member['id'], is_bot=member['is_bot']) for member in new_chat_members]
            answers = [x for x in answers if x]
            answer = answers[0] if answers else None

        elif left_chat_member:
            self.setup_left_chat_member(left_chat_member['id'], is_bot=left_chat_member['is_bot'])
        elif migrate_from_chat_id:
            answer = self.setup_new_chat_id(migrate_from_chat_id)
        elif group_chat_created:
            answer = self.group_chat_created()
        elif new_chat_title:
            self.edit_chat_title(new_chat_title)

        if answer:
            return ResponseMessage(ResponseMessageItem(text=answer))

    def setup_new_chat_member(self, member_id, is_bot):
        if is_bot:
            bot_group_id = env.int('TG_BOT_GROUP_ID')
            if member_id == bot_group_id:
                self.edit_chat_title(self.event.raw['message']['chat']['title'])
                self._set_kicked_state(False)
                return "Привет!"
        else:
            profile = self.bot.get_profile_by_user_id(member_id)
            self.bot.add_chat_to_profile(profile, self.event.chat)

    def setup_left_chat_member(self, member_id, is_bot):
        if is_bot:
            bot_group_id = env.int('TG_BOT_GROUP_ID')
            if member_id == bot_group_id:
                self._set_kicked_state(True)
        if not is_bot:
            profile = self.bot.get_profile_by_user_id(member_id)
            self.bot.remove_chat_from_profile(profile, self.event.chat)

    def setup_new_chat_id(self, chat_id):
        chat = Chat.objects.get(chat_id=chat_id)
        chat.chat_id = self.event.chat.chat_id
        chat.save()
        self.event.chat.delete()
        return "Успешно изменил id вашей группы в базе данных"

    def group_chat_created(self):
        return f"Задайте имя конфы:\n" \
               f"{self.bot.get_formatted_text_line('/конфа')} {{Название конфы}}"

    def edit_chat_title(self, new_chat_title):
        self.event.chat.name = new_chat_title
        self.event.chat.save()

    def _set_kicked_state(self, state: bool):
        self.event.chat.kicked = state
        self.event.chat.save()
