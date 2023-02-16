from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.commands.MraziCommands.Nostalgia import Nostalgia


class AdminTitle(Nostalgia):
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

    def start(self):
        if self.event.message.args:
            if len(self.event.message.args) == 1:
                title = self.event.message.args_str_case
                self.bot.set_chat_admin_title(self.event.chat.chat_id, self.event.user.user_id, title)
                return f"Поменял вашу должность на {title}"
            else:
                self.check_args(2)
                name = self.event.message.args[0]
                title = " ".join(self.event.message.args_case[1:])
                if title == '-':
                    title = self.EMPTY
                if len(title) > 16:
                    raise PWarning(f"Максимальная длина должности - 16 символов, у вас - {len(title)}")

                profile = self.bot.get_profile_by_name(name, self.event.chat)
                user_id = profile.get_user_by_platform(Platform.TG).user_id
                self.bot.set_chat_admin_title(self.event.chat.chat_id, user_id, title)
                if title == self.EMPTY:
                    return f"Сбросил должность пользователю {self.bot.get_mention(profile)}"
                else:
                    return f"Поменял должность пользователю {self.bot.get_mention(profile)} на {title}"
        else:
            self.bot.set_chat_admin_title(self.event.chat.chat_id, self.event.user.user_id, self.EMPTY)
            return f"Сбросил вашу должность"
