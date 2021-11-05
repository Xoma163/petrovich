import json

from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.Message import Message
from apps.bot.classes.messages.TgMessage import TgMessage
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment


class TgEvent(Event):

    def __init__(self, raw_event=None, bot=None):
        super().__init__(raw_event, bot)

        self.inline_mode: bool = False
        self.inline_data = {
            'query_id': None,
            'query': None,
            'offset': None
        }

    def setup_event(self, is_fwd=False):
        inline_query = self.raw.get('inline_query')
        if inline_query:
            self.setup_inline_query(inline_query)
            return

        if not is_fwd and self.raw.get('message', {}).get('forward_from'):
            self.force_not_need_a_response = True

        if is_fwd:
            message = self.raw
        else:
            edited_message = self.raw.get('edited_message')
            callback_query = self.raw.get('callback_query')
            my_chat_member = self.raw.get('my_chat_member')
            if callback_query:
                message = callback_query['message']
                message['from'] = callback_query['from']
                message['payload'] = callback_query['data']
            elif edited_message:
                message = edited_message
            elif my_chat_member:
                message = my_chat_member
            else:
                message = self.raw.get('message')

        self.peer_id = message['chat']['id']
        self.from_id = message['from']['id']

        if message['chat']['id'] != message['from']['id']:
            self.chat = self.bot.get_chat_by_id(message['chat']['id'])
            self.is_from_chat = True
        else:
            self.is_from_pm = True

        _from = message['from']
        if _from['is_bot']:
            self.is_from_bot = True
        else:
            defaults = {
                'name': _from.get('first_name'),
                'surname': _from.get('last_name'),
                'nickname': _from.get('username'),
            }
            self.user = self.bot.get_user_by_id(_from['id'], {'nickname':_from.get('username')})
            defaults.pop('nickname')
            self.sender = self.bot.get_profile_by_user(self.user, _defaults=defaults)
            self.is_from_user = True

        self.setup_action(message)
        payload = message.get('payload')
        if payload:
            self.setup_payload(payload)
        else:
            # Нет нужды парсить вложения и fwd если это просто нажатие на кнопку
            self.setup_attachments(message)
            self.setup_fwd(message.get('reply_to_message'))

        if self.sender and self.chat:
            self.bot.add_chat_to_profile(self.sender, self.chat)

    def setup_action(self, message):
        new_chat_members = message.get('new_chat_members')
        left_chat_member = message.get('left_chat_member')
        if new_chat_members:
            self.action = {'new_chat_members': new_chat_members}
        elif left_chat_member:
            self.action = {'left_chat_member': [left_chat_member]}

    def setup_payload(self, payload):
        self.payload = json.loads(payload)
        self.message = Message()
        self.message.parse_from_payload(self.payload)

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
        entities = message.get('entities')
        self.message = TgMessage(message_text, message.get('message_id'), entities) if message_text else None

    def setup_photo(self, photo_event):
        tg_photo = PhotoAttachment()
        tg_photo.parse_tg_photo(photo_event, self.bot)
        self.attachments.append(tg_photo)

    def setup_voice(self, voice_event):
        tg_voice = VoiceAttachment()
        tg_voice.parse_tg_voice(voice_event, self.bot)
        self.attachments.append(tg_voice)

    def setup_fwd(self, fwd):
        if fwd:
            fwd_event = TgEvent(fwd, self.bot)
            fwd_event.setup_event(is_fwd=True)
            self.fwd = [fwd_event]

    def setup_inline_query(self, inline_query):
        self.inline_mode = True

        message = Message(inline_query['query'])

        self.inline_data['query'] = inline_query['query']
        self.inline_data['message'] = message
        self.inline_data['id'] = inline_query['id']
        self.inline_data['offset'] = inline_query['offset']

    def need_a_response(self):
        """
        Проверка, нужен ли пользователю ответ
        """
        if self.inline_mode:
            return True
        return super().need_a_response()
