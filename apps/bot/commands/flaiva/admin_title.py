from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class AdminTitle(Command):
    name = "должность"
    names = ['title']
    help_text = "меняет должность в чате флейвы"
    help_texts = [
        "- сбрасывает вашу должность",
        "(должность) - меняет вашу должность",
        "(пользователь) (должность) - меняет должность участнику",
        "(пользователь) - - сбрасывает должность участнику"
    ]
    access = Role.FLAIVA
    platforms = [Platform.TG]
    conversation = True

    EMPTY = "ㅤ"

    bot: TgBot

    def start(self) -> ResponseMessage:
        if not self.event.message.args:
            self.bot.set_chat_admin_title(self.event.chat.chat_id, self.event.user.user_id, self.EMPTY)
            answer = "Сбросил вашу должность"
            return ResponseMessage(ResponseMessageItem(text=answer))

        if len(self.event.message.args) == 1:
            title = self.event.message.raw.split(' ', 1)[1]
            self.bot.set_chat_admin_title(self.event.chat.chat_id, self.event.user.user_id, title)
            answer = f"Поменял вашу должность на {title}"
        else:
            self.check_args(2)
            name = self.event.message.args[0]
            title = self.event.message.raw.split(' ', 2)[2]
            if title == '-':
                title = self.EMPTY
            if len(title) > 16:
                raise PWarning(f"Максимальная длина должности - 16 символов, у вас - {len(title)}")

            profile = self.bot.get_profile_by_name(name, self.event.chat)
            user_id = profile.get_tg_user().user_id
            self.bot.set_chat_admin_title(self.event.chat.chat_id, user_id, title)
            if title == self.EMPTY:
                answer = f"Сбросил должность пользователю {self.bot.get_mention(profile)}"
            else:
                answer = f"Поменял должность пользователю {self.bot.get_mention(profile)} на {title}"

        return ResponseMessage(ResponseMessageItem(text=answer))
