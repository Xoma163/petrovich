from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.commands.MraziCommands.Nostalgia import Nostalgia


class AdminTitle(Nostalgia):
    name = "должность"
    names = ['title']
    help_text = "меняет должность в чате флейвы"
    help_texts = [
        "- сбрасывает вашу должность",
        "(пользователь) (должность) - меняет должность участнику флейвы"
    ]
    access = Role.FLAIVA
    platforms = [Platform.TG]
    conversation = True

    def start(self):
        if self.event.message.args:
            self.check_args(2)
            name = self.event.message.args[0]
            title = " ".join(self.event.message.args_case[1:])
            if len(title) > 16:
                raise PWarning(f"Максимальная длина должности - 16 символов, у вас - {len(title)}")

            profile = self.bot.get_profile_by_name(name, self.event.chat)
            user_id = profile.get_user_by_platform(Platform.TG).user_id
            self.bot.set_chat_admin_title(self.event.chat.chat_id, user_id, title)
            return f"Поменял должность пользователю {profile} на {title}"
        else:
            self.bot.set_chat_admin_title(self.event.chat.chat_id, self.event.user.user_id, "")
            return f"Сбросил вашу должность"
