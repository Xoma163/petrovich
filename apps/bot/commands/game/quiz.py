from threading import Lock

from apps.bot.api.bazaotvetov import BazaOtvetov
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.poll import PollAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem

lock = Lock()


class Quiz(Command):
    name = "quiz"
    names = ["викторина"]

    help_text = HelpText(
        commands_text="начать викторину",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(None, "мини-игра, позволяющая проверить ваши знания в различных областях")
            ])
        ]
    )

    platforms = [Platform.TG]
    bot: TgBot

    def start(self) -> ResponseMessage:
        rmi = self.get_new_poll()
        if self.event.message.args:
            if self.event.message.args[0] == "еще":
                self.bot.delete_messages(self.event.peer_id, self.event.message.id)
            else:
                raise PWarning("Неверные аргументы")
        return ResponseMessage(rmi)

    def get_new_poll(self) -> ResponseMessageItem:
        bo = BazaOtvetov()
        bop = bo.get_question()

        poll = PollAttachment()
        poll.question = bop.question
        poll.options = bop.answers
        poll.type = PollAttachment.POLL_TYPE_QUIZ
        poll.correct_option_id = bop.correct_answer_index

        button = self.bot.get_button("Ещё", self.name, args=["ещё"])
        keyboard = self.bot.get_inline_keyboard([button])
        return ResponseMessageItem(attachments=[poll], keyboard=keyboard)
