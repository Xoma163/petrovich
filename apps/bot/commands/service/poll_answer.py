from threading import Lock

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import AcceptExtraCommand
from apps.bot.classes.const.consts import Platform
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.attachments.poll import PollAttachment
from apps.bot.classes.messages.attachments.poll_answer import PollAnswerAttachment

lock = Lock()


class PollAnswer(AcceptExtraCommand):
    platforms = [Platform.TG]
    bot: TgBot

    @staticmethod
    def accept_extra(event: Event) -> bool:
        return len(event.get_all_attachments([PollAnswerAttachment])) > 0

    def start(self):
        poll_answer = self.event.get_all_attachments([PollAnswerAttachment])[0]
        poll = poll_answer.poll
        if poll.type != PollAttachment.POLL_TYPE_QUIZ:
            return

        correct_answer_id = poll.correct_option_id
        user_answer = poll_answer.option_ids
        if len(user_answer) > 1:
            return
        user_answer_id = user_answer[0]

        if correct_answer_id == user_answer_id:
            self.event.sender.gamer.quiz_correct_answer_count += 1
        else:
            self.event.sender.gamer.quiz_wrong_answer_count += 1
        self.event.sender.gamer.save()
