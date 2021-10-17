import json

from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.Message import Message
from apps.bot.classes.messages.attachments.AudioAttachment import AudioAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment


class VkEvent(Event):

    def setup_event(self, is_fwd=False):
        if is_fwd:
            message = self.raw
            chat_id = None
            if message['from_id'] > 0:
                self.is_from_user = True
            else:
                self.is_from_bot = True
        else:
            message = self.raw.message
            chat_id = self.raw.chat_id

            self.is_from_chat = self.raw.from_chat
            self.is_from_user = self.raw.from_user
            self.is_from_bot = self.raw.from_group

        self.peer_id = message['peer_id']

        from_id = message['from_id']
        if from_id > 0:
            self.sender = self.bot.get_user_by_id(from_id)

        if chat_id:
            self.chat = self.bot.get_chat_by_id(chat_id)

        # self.setup_actions(message)
        payload = message.get('payload')
        if payload:
            self.setup_payload(payload)
        else:
            self.setup_attachments(message['attachments'])
            self.setup_fwd(message.get('fwd_messages') or message.get('reply_message', []))
            self.set_message(message['text'], message['id'])

    def setup_actions(self, actions):
        pass

    def setup_payload(self, payload):
        self.payload = json.loads(payload)
        self.message = Message()
        self.message.parse_from_payload(self.payload)

    def setup_attachments(self, attachments):
        routing_dict = {
            'photo': self.setup_photo,
            'video': self.setup_video,
            'audio': self.setup_audio,
            'audio_message': self.setup_voice,
        }
        for attachment in attachments:
            _type = attachment['type']
            method = routing_dict.get(_type)
            if method:
                method(attachment[_type])

    def setup_photo(self, photo):
        vk_photo = PhotoAttachment()
        vk_photo.parse_vk_photo(photo)
        self.attachments.append(vk_photo)

    def setup_video(self, video):
        vk_video = VideoAttachment()
        vk_video.parse_vk_video(video)
        self.attachments.append(vk_video)

    def setup_audio(self, video):
        vk_audio = AudioAttachment()
        vk_audio.parse_vk_audio(video)
        self.attachments.append(vk_audio)

    def setup_voice(self, voice):
        vk_voice = VoiceAttachment()
        vk_voice.parse_vk_voice(voice)
        self.attachments.append(vk_voice)

    def setup_fwd(self, fwd):
        if not isinstance(fwd, list):
            fwd = [fwd]
        for fwd_message in fwd:
            fwd_event = VkEvent(fwd_message, self.bot)
            fwd_event.setup_event(is_fwd=True)
            self.fwd.append(fwd_event)
