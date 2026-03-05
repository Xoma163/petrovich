from apps.bot.consts import RoleEnum
from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.shared.exceptions import PSkip, PWarning
from apps.shared.utils.cache import MessagesCache
from petrovich.settings import env


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
        peer_id = self.event.peer_id
        message_id = self.event.fwd[0].message.id
        new_text = self.event.message.args_str

        if self.event.fwd[0].raw['from']['username'] != env.str("TG_BOT_LOGIN"):
            raise PWarning("Я могу редактировать только свои сообщения")

        rmi = ResponseMessageItem(peer_id=peer_id, message_id=message_id, text=new_text)
        self.bot.edit_message_text(rmi)

        mc = MessagesCache(peer_id)
        cached_messages = mc.get_messages()

        if cached_message := cached_messages.get(message_id, None):
            cached_message['text'] = new_text
            mc.set_message(message_id, cached_message)

        raise PSkip()
