from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class AdminTitle(Command):
    name = "должность"
    names = ['title']

    help_text = HelpText(
        commands_text="меняет должность в чате флейвы",
        help_texts=[
            HelpTextItem(Role.FLAIVA, [
                HelpTextArgument(None, "сбрасывает вашу должность"),
                HelpTextArgument("(должность)", "меняет вашу должность"),
                HelpTextArgument("(пользователь) (должность)", "меняет должность участнику"),
                HelpTextArgument("(пользователь)", "сбрасывает должность участнику")
            ])
        ]
    )

    access = Role.FLAIVA
    platforms = [Platform.TG]
    conversation = True

    EMPTY = "ㅤ"

    bot: TgBot

    def start(self) -> ResponseMessage:
        if not self.event.message.args:
            self.change_title(self.event.sender, self.EMPTY)
            answer = "Сбросил вашу должность"
            return ResponseMessage(ResponseMessageItem(text=answer))

        if len(self.event.message.args) == 1:
            title = self.event.message.raw.split(' ', 1)[1]
            self.change_title(self.event.sender, title)
            answer = f"Поменял вашу должность на \"{title}\""
        else:
            self.check_args(2)
            name = self.event.message.args[0]
            profile = self.bot.get_profile_by_name([name], self.event.chat)
            title = self.event.message.raw.split(' ', 2)[2]
            if title == '-':
                title = self.EMPTY
            self.change_title(profile, title)
            if title == self.EMPTY:
                answer = f"Сбросил должность пользователю {self.bot.get_mention(profile)}"
            else:
                answer = f"Поменял должность пользователю {self.bot.get_mention(profile)} на \"{title}\""

        return ResponseMessage(ResponseMessageItem(text=answer))

    def change_title(self, profile, title):
        if len(title) > 16:
            raise PWarning(f"Максимальная длина должности - 16 символов, у вас - {len(title)}")
        self.bot.set_chat_admin_title(self.event.chat.chat_id, profile.get_tg_user().user_id, title)
