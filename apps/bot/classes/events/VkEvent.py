import json

from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.Message import Message
from apps.bot.classes.messages.attachments.AudioAttachment import AudioAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.StickerAttachment import StickerAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.classes.messages.attachments.VoiceAttachment import VoiceAttachment


class VkEvent(Event):

    def setup_event(self, is_fwd=False):
        if is_fwd:
            message = self.raw
            chat_id = None
            self.peer_id = message.get('peer_id')
            # Вк на репли сообщение стал слать второй ивент зачем-то
            if not self.peer_id:
                self.force_response = False
                return
            self.from_id = message['from_id']
            if self.from_id > 0:
                self.is_from_user = True
            else:
                self.is_from_bot = True

        else:
            message = self.raw.message
            chat_id = self.raw.chat_id

            self.is_from_chat = self.raw.from_chat
            self.is_from_user = self.raw.from_user
            self.is_from_bot = self.raw.from_group or self.raw.message.from_id < 0

            self.from_id = message['from_id']
            self.peer_id = message['peer_id']

        if self.from_id == self.peer_id:
            self.is_from_pm = True

        from_id = message['from_id']
        if from_id > 0:
            self.user = self.bot.get_user_by_id(from_id)
            self.sender = self.bot.get_profile_by_user(self.user)

        if chat_id:
            self.chat = self.bot.get_chat_by_id(2000000000 + chat_id)

        self.setup_action(message.get('action'))
        payload = message.get('payload')
        if payload:
            self.setup_payload(payload)
        else:
            is_cropped = message.get('is_cropped')
            if is_cropped:
                conversation_message_id = message['conversation_message_id']
                message = self.bot.get_conversation_messages(self.peer_id, conversation_message_id)
            self.setup_attachments(message['attachments'])
            self.setup_fwd(message.get('fwd_messages') or message.get('reply_message', []))
            self.set_message(message['text'], message['id'])

        if self.sender and self.chat:
            self.bot.add_chat_to_profile(self.sender, self.chat)

    def setup_action(self, action):
        if not action:
            return
        _type = action.get('type', None)
        body = {
            'id': action['member_id'] if action['member_id'] > 0 else -action['member_id'],
            'is_bot': action['member_id'] < 0
        }

        if _type in ['chat_invite_user', 'chat_invite_user_by_link']:
            self.action = {
                'new_chat_members': [body]
            }
        elif _type in ['chat_kick_user']:
            self.action = {
                'left_chat_member': [body]
            }

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
            'sticker': self.setup_sticker
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

    def setup_sticker(self, sticker):
        vk_sticker = StickerAttachment()
        vk_sticker.parse_vk_sticker(sticker)
        self.attachments.append(vk_sticker)

    def setup_fwd(self, fwd):
        if not isinstance(fwd, list):
            fwd = [fwd]
        for fwd_message in fwd:
            fwd_event = VkEvent(fwd_message, self.bot)
            fwd_event.setup_event(is_fwd=True)
            self.fwd.append(fwd_event)
