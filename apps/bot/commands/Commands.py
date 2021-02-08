from apps.bot.classes.Consts import Role
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_role_by_str


class Commands(CommonCommand):
    names = ["команды"]
    help_text = "Команды - список всех команд"
    detail_help_text = "Команды - список всех команд\n" \
                       "Команды (название роли) - список команд для роли"

    def start(self):
        from apps.bot.initial import HELP_TEXTS

        help_texts = HELP_TEXTS[self.event.platform]
        ordered_roles = [
            {"role": Role.USER, "text": "общие команды"},
            {"role": Role.ADMIN, "text": "команды для администраторов"},
            {"role": Role.MODERATOR, "text": "команды для модераторов"},
            {"role": Role.MINECRAFT, "text": "команды для игроков майнкрафта"},
            {"role": Role.TRUSTED, "text": "команды для доверенных пользователей"},
            {"role": Role.STUDENT, "text": "команды для студентов"},
            {"role": Role.MINECRAFT_NOTIFY, "text": "команды для уведомлённых майнкрафтеров"},
            {"role": Role.TERRARIA, "text": "команды для игроков террарии"},
            {"role": Role.HOME, "text": "команды для домашних пользователей"},
        ]

        if self.event.args:
            role = get_role_by_str(self.event.original_args.lower())
            if not role:
                raise PWarning("Не знаю такой роли")
            for ordered_role in ordered_roles:
                if ordered_role['role'] == role:
                    result = self.get_str_for_role(help_texts, ordered_role)
                    if not result:
                        return "У вас нет прав для просмотра команд данной роли"
                    return result
            return "У данной роли нет списка команд"

        output = ""
        for role in ordered_roles:
            output += self.get_str_for_role(help_texts, role)
        if 'games' in help_texts:
            output += "\n\n— игры —\n"
            output += help_texts['games']
        output = output.rstrip()
        return output

    def get_str_for_role(self, help_texts, role):
        result = ""
        if self.event.sender.check_role(role['role']) and help_texts[role['role'].name]:
            result += f"\n\n— {role['text']} —\n"
            result += help_texts[role['role'].name]
        return result
