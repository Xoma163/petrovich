from apps.bot.core.event.event import Event
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Chat
from apps.bot.utils import remove_profile_from_chat, get_profile_by_user_id, add_profile_to_chat
from apps.commands.command import Command
from petrovich.settings import env


class Actions(Command):
    names = None
    # Обоснование: команда должна запускаться с максимальным приоритетом из-за экшенов
    priority = 100

    def accept(self, event: Event) -> bool:
        return bool(event.action)

    def start(self) -> ResponseMessage | None:
        my_chat_member = self.event.action.get('my_chat_member')
        chat_member = self.event.action.get('chat_member')
        new_chat_members = self.event.action.get('new_chat_members')
        left_chat_member = self.event.action.get('left_chat_member')
        migrate_from_chat_id = self.event.action.get('migrate_from_chat_id')
        group_chat_created = self.event.action.get('group_chat_created')
        new_chat_title = self.event.action.get('new_chat_title')

        forum_topic_created = self.event.action.get('forum_topic_created')
        forum_topic_edited = self.event.action.get('forum_topic_edited')

        answer = None
        if new_chat_members:
            answers = [self.setup_new_chat_member(member['id'], is_bot=member['is_bot']) for member in new_chat_members]
            answers = [x for x in answers if x]
            answer = answers[0] if answers else None

        elif left_chat_member:
            self.setup_left_chat_member(left_chat_member)
        elif migrate_from_chat_id:
            answer = self.setup_new_chat_id(migrate_from_chat_id)
        elif group_chat_created:
            answer = self.group_chat_created()
        elif new_chat_title:
            self.edit_chat_title(new_chat_title)
        elif my_chat_member or chat_member:
            self.chat_member(my_chat_member or chat_member)
        elif forum_topic_created:
            self.create_forum_topic(forum_topic_created)
        elif forum_topic_edited:
            self.edit_forum_topic(forum_topic_edited)

        if answer:
            return ResponseMessage(ResponseMessageItem(text=answer))
        return None

    def setup_new_chat_member(self, member_id, is_bot):
        if is_bot:
            bot_group_id = env.int('TG_BOT_GROUP_ID')
            if member_id == bot_group_id:
                self.edit_chat_title(self.event.raw['message']['chat']['title'])
                self._set_kicked_state(False)
                return "Привет!"
            return None
        else:
            profile = get_profile_by_user_id(member_id, self.bot.platform)
            add_profile_to_chat(profile, self.event.chat)
            return None

    def setup_left_chat_member(self, left_chat_member):
        is_bot = left_chat_member['is_bot']
        user_id = left_chat_member['id']

        if is_bot:
            bot_group_id = env.int('TG_BOT_GROUP_ID')
            if user_id == bot_group_id:
                self._set_kicked_state(True)
        if not is_bot:
            profile = get_profile_by_user_id(user_id, self.bot.platform)
            remove_profile_from_chat(profile, self.event.chat)

    def setup_new_chat_id(self, chat_id):
        # Если новый чат каким-то чудом создался - удаляем его
        self.event.chat.delete()

        # Переносим вручную
        chat = Chat.objects.get(chat_id=chat_id)
        chat.chat_id = self.event.chat.chat_id
        chat.save()
        return "Успешно изменил id вашей группы в базе данных"

    def group_chat_created(self):
        self.edit_chat_title(self.event.raw['message']['chat']['title'])
        return "Привет!"

    def edit_chat_title(self, new_chat_title):
        self.event.chat.name = new_chat_title
        self.event.chat.save()

    def _set_kicked_state(self, state: bool):
        # status kicked в my_chat_member == бота забанили
        if not self.event.chat:
            return
        self.event.chat.kicked = state
        self.event.chat.save()

    def chat_member(self, chat_member):
        chat_member = chat_member['new_chat_member']
        status = chat_member['status']
        if status in ["left", "kicked"]:
            self.setup_left_chat_member(chat_member['user'])

    # ToDo: peer_id + message_thread_id
    def create_forum_topic(self, forum_topic_created):
        pass

    # ToDo: здесь получаем только имя. peer_id + message_thread_id нужно брать из ивента
    def edit_forum_topic(self, forum_topic_edited):
        pass
