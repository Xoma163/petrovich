from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class PromoteAdmin(Command):
    name = "promote"
    access = Role.FLAIVA
    platforms = [Platform.TG]
    conversation = True

    bot: TgBot

    def start(self) -> ResponseMessage:
        profile = self.bot.get_profile_by_name(self.event.message.args, self.event.chat)
        user_id = profile.get_tg_user().user_id
        res = self.bot.promote_chat_member(self.event.chat.chat_id, user_id)
        if res['ok']:
            answer = f"Выдал права админа для пользователя {profile}"
            return ResponseMessage(ResponseMessageItem(text=answer))
        else:
            error = f"Ошибка выдачи прав админа для пользователя {profile}"
            raise PWarning(error)
