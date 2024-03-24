import json

from apps.bot.classes.const.consts import Platform
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.gif import GifAttachment
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.attachments.sticker import StickerAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.attachments.videonote import VideoNoteAttachment
from apps.bot.classes.messages.attachments.voice import VoiceAttachment
from apps.bot.classes.messages.message import Message
from apps.bot.classes.messages.tg.message import TgMessage
from petrovich.settings import env


class TgEvent(Event):

    def __init__(self, raw_event=None):
        from apps.bot.classes.bots.tg_bot import TgBot
        super().__init__(raw_event)
        self.bot = TgBot()
        self.platform = Platform.TG

        self.inline_mode: bool = False

        self.inline_data = {
            'query_id': None,
            'query': None,
            'offset': None
        }

    def setup_event(self, **kwargs):
        self.is_fwd = kwargs.get("is_fwd", False)
        inline_query = self.raw.get('inline_query')
        if inline_query:
            self.setup_inline_query(inline_query)
            return

        fwd_message_without_voice = False
        if not self.is_fwd and self.raw.get('message', {}).get('forward_from') and 'voice' not in self.raw.get(
                'message', {}):
            fwd_message_without_voice = True

        if self.is_fwd:
            message = self.raw
        else:
            callback_query = self.raw.get('callback_query')
            my_chat_member = self.raw.get('my_chat_member')
            edited_message = self.raw.get('edited_message')
            poll_answer = self.raw.get('poll_answer')
            poll = self.raw.get('poll')

            if callback_query:
                message = callback_query['message']
                message['from'] = callback_query['from']
                message['payload'] = callback_query['data']
            elif edited_message:
                return
                # message = edited_message
            elif my_chat_member:
                message = my_chat_member
            elif poll_answer:
                return
            elif poll:
                return
            else:
                message = self.raw.get('message')
        if not message:
            return

            # if not message:
            #     message = self.raw

        is_topic_message = message.get('is_topic_message')
        if is_topic_message:
            self.message_thread_id = message.get('message_thread_id')

        self.peer_id = message['chat']['id']
        self.from_id = message['from']['id']

        if message['chat']['type'] == 'private':
            self.is_from_pm = True
        elif message['chat']['type'] in ["group", "supergroup", "channel"]:
            self.chat = self.bot.get_chat_by_id(message['chat']['id'])
            self.is_from_chat = True

        if self.is_fwd:
            _from = message.get('forward_from', message['from'])
        else:
            _from = message['from']

        if _from['is_bot']:
            self.is_from_bot = True
            if _from['id'] == env.int('TG_BOT_GROUP_ID'):
                self.is_from_bot_me = True

        else:
            defaults = {
                'name': _from.get('first_name'),
                'surname': _from.get('last_name'),
                'nickname': _from.get('username'),
            }
            self.user = self.bot.get_user_by_id(_from['id'], {'nickname': _from.get('username')})
            defaults.pop('nickname')
            self.sender = self.bot.get_profile_by_user(self.user, _defaults=defaults)
            self.is_from_user = True

        self.setup_action(message)
        payload = message.get('payload')
        # Нет нужды парсить вложения и fwd если это просто нажатие на кнопку
        if payload:
            # Если у нас не уместилось содержимое в кнопку и сраные 64 байта, то мы берём и парсим прям текст кнопки
            first_button_text = message['reply_markup']['inline_keyboard'][0][0]['text']
            self.setup_payload(payload, first_button_text)
            if self.message.raw:
                self.setup_attachments(message, self.message.raw)
        else:
            self.setup_attachments(message)
            self.setup_fwd(message.get('reply_to_message'))
            if message.get('forward_from_chat'):
                self.is_fwd = True

        forward_from_chat = message.get('forward_from_chat')
        if forward_from_chat:
            self.force_response = False

        via_bot = message.get('via_bot')
        if via_bot and via_bot['username'] == env.str("TG_BOT_LOGIN"):
            self.force_response = False

        if self.sender and self.chat and not self.is_fwd:
            self.bot.add_chat_to_profile(self.sender, self.chat)

        if fwd_message_without_voice:
            need_a_response_extra = self.need_a_response_extra()
            if not need_a_response_extra:
                self.force_response = False

        super().setup_event(**kwargs)

    def setup_action(self, message):
        actions = [
            'new_chat_members', "left_chat_member", "migrate_from_chat_id", "group_chat_created", "new_chat_title"
        ]
        for action in actions:
            if action in message:
                self.action[action] = message[action]

        actions_raw = ["my_chat_member", "chat_member"]
        for action in actions_raw:
            if action in self.raw:
                self.action[action] = self.raw[action]

    def setup_payload(self, payload, first_button_text):
        self.message = Message()
        try:
            self.payload = json.loads(payload)
            if not self.payload and not first_button_text:
                self.force_response = False
                return
            if self.payload:
                self.message.parse_from_payload(self.payload)
            elif first_button_text:
                self.message.parse_raw(first_button_text)

        except Exception:
            self.message.parse_raw(payload)

    def setup_attachments(self, message, payload_message_text=None):
        photo = message.get('photo')
        video = message.get('video')
        video_note = message.get('video_note')
        gif = message.get('animation')
        voice = message.get('voice')
        document = message.get('document')
        sticker = message.get('sticker')
        audio = message.get('audio')
        message_text = None
        if voice:
            self.setup_voice(voice)
        elif photo:
            self.setup_photo(photo[-1])
            message_text = message.get('caption')
        elif video:
            self.setup_video(video)
            message_text = message.get('caption')
        elif video_note:
            self.setup_video_note(video_note)
        elif gif:
            self.setup_gif(gif)
            message_text = message.get('caption')
        elif document:
            if document['mime_type'] in ['image/png', 'image/jpg', 'image/jpeg']:
                self.setup_photo(document)
                message_text = message.get('caption')
        elif sticker:
            self.setup_sticker(sticker)
        elif audio:
            self.setup_audio(audio)
        else:
            message_text = message.get('text')

        if payload_message_text:
            message_text = payload_message_text

        if message_text:
            self.setup_link(message_text)
        entities = message.get('entities') or message.get('caption_entities')
        self.message = TgMessage(message_text, message.get('message_id'), entities, quote=message.get('quote'))

    def setup_photo(self, photo_event):
        tg_photo = PhotoAttachment()
        tg_photo.parse_tg(photo_event)
        self.attachments.append(tg_photo)

    def setup_video(self, video_event):
        tg_video = VideoAttachment()
        tg_video.parse_tg(video_event)
        self.attachments.append(tg_video)

    def setup_video_note(self, video_event):
        tg_video = VideoNoteAttachment()
        tg_video.parse_tg(video_event)
        self.attachments.append(tg_video)

    def setup_gif(self, gif_event):
        tg_gif = GifAttachment()
        tg_gif.parse_tg(gif_event)
        self.attachments.append(tg_gif)

    def setup_voice(self, voice_event):
        tg_voice = VoiceAttachment()
        tg_voice.parse_tg(voice_event)
        self.attachments.append(tg_voice)

    def setup_sticker(self, sticker_event):
        tg_sticker = StickerAttachment()
        tg_sticker.parse_tg(sticker_event)
        self.attachments.append(tg_sticker)

    def setup_audio(self, audio_event):
        tg_audio = AudioAttachment()
        tg_audio.parse_tg(audio_event)
        self.attachments.append(tg_audio)

    def setup_link(self, text):
        res = LinkAttachment.parse_link(text)
        for url in res:
            link = LinkAttachment()
            link.url = url
            self.attachments.append(link)

    def setup_fwd(self, fwd):
        if fwd:
            if fwd.get('message_id') == fwd.get('message_thread_id'):
                return
            fwd_event = TgEvent(fwd)
            fwd_event.setup_event(is_fwd=True)
            self.fwd = [fwd_event]

    def setup_inline_query(self, inline_query):
        self.inline_mode = True

        message = Message(inline_query['query'])

        self.inline_data['query'] = inline_query['query']
        self.inline_data['message'] = message
        self.inline_data['id'] = inline_query['id']
        self.inline_data['offset'] = inline_query['offset']

        _from = inline_query['from']
        defaults = {
            'name': _from.get('first_name'),
            'surname': _from.get('last_name')
        }
        self.user = self.bot.get_user_by_id(_from['id'], {'nickname': _from.get('username')})
        self.sender = self.bot.get_profile_by_user(self.user, _defaults=defaults)
        self.is_from_user = True

    def need_a_response(self):
        """
        Проверка, нужен ли пользователю ответ
        """
        if self.inline_mode:
            return True
        return super().need_a_response()
