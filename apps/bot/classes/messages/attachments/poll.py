from typing import Optional

from apps.bot.classes.messages.attachments.attachment import Attachment


class PollAttachment(Attachment):
    TYPE = "poll"

    POLL_TYPE_QUIZ = "quiz"
    POLL_TYPE_REGULAR = "regular"

    def __init__(self):
        super().__init__(self.TYPE)
        self.id: Optional[str] = None
        self.question: str = ""
        self.options: list[str] = []
        self.is_anonymous: bool = False
        self.type: str = self.POLL_TYPE_REGULAR
        self.allows_multiple_answers: bool = False

    def parse_tg(self, event):
        pass

    def parse_tg_poll_answer(self, event):
        self.id = event['poll_id']
