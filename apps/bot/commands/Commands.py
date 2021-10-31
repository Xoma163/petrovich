from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import get_role_by_str


class Commands(Command):
    name = "команды"
    name_tg = "commands"
    help_text = "список всех команд"
    help_texts = [
        "- список всех команд",
        "(название роли) - список команд для роли"
    ]

    def start(self):
        from apps.bot.initial import HELP_TEXTS

        help_texts = HELP_TEXTS[self.event.platform]
        ordered_roles = [
            {"role": Role.USER, "text": "общие команды"},
            {"role": Role.ADMIN, "text": "команды для администраторов"},
            {"role": Role.MODERATOR, "text": "команды для модераторов"},
            {"role": Role.MINECRAFT, "text": "команды для игроков майнкрафта"},
            {"role": Role.TRUSTED, "text": "команды для доверенных пользователей"},
            {"role": Role.MINECRAFT_NOTIFY, "text": "команды для уведомлённых майнкрафтеров"},
            {"role": Role.TERRARIA, "text": "команды для игроков террарии"},
            {"role": Role.HOME, "text": "команды для домашних пользователей"},
            {"role": Role.MRAZ, "text": "команды для мразей"},
        ]

        if self.event.message.args:
            role = get_role_by_str(self.event.message.args_str)
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
            output += "\n— игры —\n"
            if self.event.platform == Platform.TG:
                output += f"```\n{help_texts['games']}\n```"
            else:
                output += help_texts['games']
        output = output.rstrip()
        if self.event.platform == Platform.TG:
            return {'text': output, "parse_mode": "markdown"}
        return output

    def get_str_for_role(self, help_texts, role):
        result = ""
        if self.event.sender.check_role(role['role']) and help_texts[role['role'].name]:
            result += f"\n— {role['text']} —\n"
            if self.event.platform == Platform.TG:
                result += f"```\n{help_texts[role['role'].name]}\n```"
            else:
                result += help_texts[role['role'].name]
        return result
