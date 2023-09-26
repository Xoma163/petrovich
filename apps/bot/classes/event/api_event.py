from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.attachments.photo import PhotoAttachment


class APIEvent(Event):
    def setup_event(self, is_fwd=False):
        text = self.raw['text']
        self.sender = self.raw['profile']
        self.user = self.sender.user.instance
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
        tg_photo.parse_api(photo_event)
        self.attachments.append(tg_photo)
