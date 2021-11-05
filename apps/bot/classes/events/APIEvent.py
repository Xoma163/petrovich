from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment


class APIEvent(Event):
    def setup_event(self, is_fwd=False):
        user_id = self.raw['token']
        text = self.raw['text']

        self.user = self.bot.get_user_by_id(user_id)
        self.sender = self.bot.get_profile_by_user(self.user)
        self.is_from_user = True
        self.is_from_pm = True
        self.set_message(text)
        attachments = self.raw.get('attachments', [])
        self.setup_attachments(attachments)

    def setup_attachments(self, attachments: list):
        for att_type in attachments:
            att = attachments[att_type]
            if att_type == 'photo':
                self.setup_photo(att)

    def setup_photo(self, photo_event):
        tg_photo = PhotoAttachment()
        tg_photo.parse_api_photo(photo_event)
        self.attachments.append(tg_photo)
