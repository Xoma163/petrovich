from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.utils.cache import PollCache


class PollAttachment(Attachment):
    TYPE = "poll"

    POLL_TYPE_QUIZ = "quiz"
    POLL_TYPE_REGULAR = "regular"

    def __init__(self):
        super().__init__(self.TYPE)
        self.tg_id: str | None = None
        self.question: str = ""
        self.options: list[str] = []
        self.options_with_votes: list[str] = []
        self.is_anonymous: bool = False
        self.poll_type: str = self.POLL_TYPE_REGULAR
        self.allows_multiple_answers: bool = False

        self.correct_option_id: int | None = None

    def parse_tg(self, event):
        self.tg_id = event['id']
        self.question = event['question']
        self.options = [x['text'] for x in event['options']]
        self.options_with_votes = event['options']
        self.is_anonymous = event['is_anonymous']
        self.poll_type = event['type']
        self.allows_multiple_answers = event['allows_multiple_answers']
        self.correct_option_id = event.get('correct_option_id')

    def set_by_tg_id(self, tg_id):
        pc = PollCache(tg_id)
        poll = pc.get_poll()
        self.parse_tg(poll)
