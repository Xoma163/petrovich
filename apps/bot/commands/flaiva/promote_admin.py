from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Chat


class PromoteAdmin(Command):
    name = "promote"
    access = Role.FLAIVA
    platforms = [Platform.TG]
    conversation = True

    bot: TgBot

    def start(self) -> ResponseMessage:
        chat = Chat.objects.get(pk=46)
        profile = self.bot.get_profile_by_name(self.event.message.args, chat)
        user_id = profile.get_tg_user().user_id
        self.bot.promote_chat_member(self.event.chat.chat_id, user_id)
        answer = "done"

        return ResponseMessage(ResponseMessageItem(text=answer))
