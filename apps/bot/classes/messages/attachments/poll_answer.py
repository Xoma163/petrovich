from apps.bot.classes.messages.attachments.attachment import Attachment
from apps.bot.classes.messages.attachments.poll import PollAttachment


class PollAnswerAttachment(Attachment):
    TYPE = "poll_answer"

    def __init__(self):
        super().__init__(self.TYPE)
        self.poll: PollAttachment = PollAttachment()
        self.option_ids: list = []

    def parse_tg(self, event):
        self.poll.set_by_tg_id(event['poll_id'])
        self.option_ids = event['option_ids']
