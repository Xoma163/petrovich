import json

from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.Message import Message
from apps.bot.classes.messages.TgMessage import TgMessage
from apps.bot.classes.messages.attachments.AudioAttachment import AudioAttachment
from apps.bot.classes.messages.attachments.GifAttachment import GifAttachment
from apps.bot.classes.messages.attachments.LinkAttachment import LinkAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.StickerAttachment import StickerAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.classes.messages.attachments.VideoNoteAttachment import VideoNoteAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment
from petrovich.settings import env


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
        self.is_fwd = is_fwd
        inline_query = self.raw.get('inline_query')
        if inline_query:
            self.setup_inline_query(inline_query)
            return

        fwd_message_without_voice = False
        if not self.is_fwd and self.raw.get('message', {}).get('forward_from') and 'voice' not in self.raw['message']:
            # self.force_response = False
            fwd_message_without_voice = True

        if self.is_fwd:
            message = self.raw
        else:
            # edited_message = self.raw.get('edited_message')
            callback_query = self.raw.get('callback_query')
            my_chat_member = self.raw.get('my_chat_member')
            edited_message = self.raw.get('edited_message')
            if callback_query:
                message = callback_query['message']
                message['from'] = callback_query['from']
                message['payload'] = callback_query['data']
            elif edited_message:
                self.force_response = False
                return
                # message = edited_message
            elif my_chat_member:
                message = my_chat_member
            else:
                message = self.raw.get('message')
        is_topic_message = message.get('is_topic_message')
        if is_topic_message:
            self.message_thread_id = message.get('message_thread_id')

        self.peer_id = message['chat']['id']
        self.from_id = message['from']['id']

        if message['chat']['id'] != message['from']['id']:
            self.chat = self.bot.get_chat_by_id(message['chat']['id'])
            self.is_from_chat = True
        else:
            self.is_from_pm = True

        if self.is_fwd:
            _from = message.get('forward_from', message['from'])
        else:
            _from = message['from']
        if _from['is_bot']:
            self.is_from_bot = True
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

        via_bot = message.get('via_bot')
        if via_bot:
            if via_bot['username'] == env.str("TG_BOT_LOGIN"):
                self.force_response = False

        if self.sender and self.chat and not self.is_fwd:
            self.bot.add_chat_to_profile(self.sender, self.chat)

        if fwd_message_without_voice:
            need_a_response_extra = self.need_a_response_extra()
            if not need_a_response_extra:
                self.force_response = False
                return

    def setup_action(self, message):
        new_chat_members = message.get('new_chat_members')
        left_chat_member = message.get('left_chat_member')
        migrate_from_chat_id = message.get('migrate_from_chat_id')
        group_chat_created = message.get('group_chat_created')
        if new_chat_members:
            self.action = {'new_chat_members': new_chat_members}
        elif left_chat_member:
            self.action = {'left_chat_member': left_chat_member}
        elif migrate_from_chat_id:
            self.action = {'migrate_from_chat_id': migrate_from_chat_id}
        elif group_chat_created:
            self.action = {'group_chat_created': group_chat_created}

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

        except:
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
        entities = message.get('entities')
        self.message = TgMessage(message_text, message.get('message_id'), entities)

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
        res = LinkAttachment.parse(text)
        for url in res:
            link = LinkAttachment()
            link.url = url
            self.attachments.append(link)

    def setup_fwd(self, fwd):
        if fwd:
            if fwd.get('message_id') == fwd.get('message_thread_id'):
                return
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
