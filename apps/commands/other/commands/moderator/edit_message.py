from apps.bot.consts import RoleEnum
from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.bot.core.messages.response_message import ResponseMessage
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.shared.exceptions import PSkip


class EditMessage(Command):
    name = "edit_message"
    access = RoleEnum.MODERATOR
    help_text = HelpText(
        commands_text="редактирование сообщения бота",
        help_texts=[
            HelpTextItem(RoleEnum.MODERATOR, [
                HelpTextArgument("edit_message (пересланное сообщение) (новый текст)", "изменяет текст в сообщении"),
            ])
        ]
    )
    args = 1
    fwd = True
    priority = 1

    bot: TgBot

    def start(self) -> ResponseMessage:
        self.bot.edit_message(
            {'chat_id': self.event.peer_id, 'message_id': self.event.fwd[0].message.id,
             'text': self.event.message.args_str}
        )
        raise PSkip()
