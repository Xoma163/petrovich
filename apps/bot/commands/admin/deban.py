from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class DeBan(Command):
    name = "разбан"
    help_text = HelpText(
        commands_text="разбан пользователя",
        help_texts=[
            HelpTextItem(Role.ADMIN, [
                HelpTextItemCommand("(N)", "разбан пользователя, где N - имя, фамилия, логин/id, никнейм")
            ])
        ]
    )
    access = Role.ADMIN
    args = 1

    def start(self) -> ResponseMessage:
        profile = self.bot.get_profile_by_name(self.event.message.args, self.event.chat)
        profile.remove_role(Role.BANNED)

        answer = f"{profile} разбанена" if profile.is_female else f"{profile} разбанен"
        return ResponseMessage(ResponseMessageItem(text=answer))
