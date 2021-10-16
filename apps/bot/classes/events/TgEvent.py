from django.contrib.auth.models import Group

from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.Message import Message
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment
from apps.bot.models import Users


class TgEvent(Event):

    def setup_event(self, is_fwd=False):
        if self.raw.get('forward_from'):
            return

        if is_fwd:
            message = self.raw
        else:
            edited_message = self.raw.get('edited_message')
            if edited_message:
                message = edited_message
            else:
                message = self.raw.get('message')
        if not message:
            return

        self.peer_id = str(message['chat']['id'])

        if message['chat']['id'] != message['from']['id']:
            self.chat = self.bot.get_chat_by_id(message['chat']['id'])
            self.is_from_chat = True
        else:
            self.is_from_user = True
        if message['from']['is_bot']:
            self.is_from_bot = True

        self.setup_attachments(message)
        self.setup_fwd(message.get('reply_to_message'))
        self.sender = self.register_user(message['from'])

    def register_user(self, user) -> Users:
        """
        Регистрация пользователя если его нет в БД
        Почти аналог get_user_by_id в VkBot, только у ТГ нет метода для получения данных о пользователе,
        поэтому метод немного другой
        """

        def set_fields(_user):
            _user.name = user.get('first_name', None)
            _user.surname = user.get('last_name', None)
            _user.nickname = user.get('username', None)
            _user.platform = self.platform.name
            _user.save()
            group_user = Group.objects.get(name=Role.USER.name)
            _user.groups.add(group_user)
            _user.save()

        tg_user = self.bot.user_model.filter(user_id=user['id'])
        if tg_user.count() > 0:
            tg_user = tg_user.first()

            if tg_user.name is None:
                set_fields(tg_user)
        else:
            tg_user = Users()
            tg_user.user_id = user['id']
            set_fields(tg_user)
        return tg_user

    def setup_attachments(self, message):
        photo = message.get('photo')
        voice = message.get('voice')
        document = message.get('document')
        message_text = None
        if voice:
            self.setup_voice(voice)
        elif photo:
            self.setup_photo(photo[-1])
            message_text = message.get('caption')
        elif document:
            if document['mime_type'] in ['image/png', 'image/jpg', 'image/jpeg']:
                self.setup_photo(document)
                message_text = message.get('caption')
        else:
            message_text = message.get('text')
        self.message = Message(message_text, message['message_id']) if message_text else None

    def setup_fwd(self, fwd):
        if fwd:
            fwd_event = TgEvent(fwd, self.bot)
            fwd_event.setup_event(is_fwd=True)
            self.fwd = [fwd_event]

    def setup_photo(self, photo_event):
        tg_photo = PhotoAttachment()
        tg_photo.parse_tg_photo(photo_event, self.bot)
        self.attachments.append(tg_photo)

    def setup_voice(self, voice_event):
        tg_voice = VoiceAttachment()
        tg_voice.parse_tg_voice(voice_event, self.bot)
        self.attachments.append(tg_voice)
