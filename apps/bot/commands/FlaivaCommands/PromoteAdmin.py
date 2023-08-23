from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class PromoteAdmin(Command):
    name = "promote"
    access = Role.FLAIVA
    platforms = [Platform.TG]
    conversation = True

    bot: TgBot

    def start(self):
        name = self.event.message.args[0]
        profile = self.bot.get_profile_by_name(name, self.event.chat)
        user_id = profile.get_tg_user().user_id
        self.bot.promote_chat_member(self.event.chat.chat_id, user_id)
        answer = "done"

        return ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id
            )
        )
