from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Ban(Command):
    name = "бан"
    help_text = HelpText(
        commands_text="бан пользователя",
        help_texts=[
            HelpTextItem(Role.ADMIN, [
                HelpTextArgument("(N)", "бан пользователя, где N - имя, фамилия, логин/id, никнейм")
            ])
        ]
    )

    access = Role.ADMIN
    args = 1

    def start(self) -> ResponseMessage:
        profile = self.bot.get_profile_by_name(self.event.message.args, self.event.chat)
        if profile.check_role(Role.ADMIN):
            raise PWarning("Нельзя банить админа")
        profile.add_role(Role.BANNED)

        answer = f"{profile} забанена" if profile.is_female else f"{profile} забанен"
        return ResponseMessage(ResponseMessageItem(text=answer))
