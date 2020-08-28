from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class Commands(CommonCommand):
    def __init__(self):
        names = ["команды"]
        help_text = "Команды - список всех команд"
        super().__init__(names, help_text)

    def start(self):
        from apps.bot.initial import API_HELP_TEXT, HELP_TEXT

        if self.event.platform == 'api':
            help_texts = API_HELP_TEXT
        else:
            help_texts = HELP_TEXT

        ordered_roles = [
            {"role": Role.USER, "text": "общие команды"},
            {"role": Role.ADMIN, "text": "команды для администраторов"},
            {"role": Role.MODERATOR, "text": "команды для модераторов"},
            {"role": Role.MINECRAFT, "text": "команды для игроков майнкрафта"},
            {"role": Role.TRUSTED, "text": "команды для доверенных пользователей"},
            {"role": Role.STUDENT, "text": "команды для группы 6221"},
            {"role": Role.MINECRAFT_NOTIFY, "text": "команды для уведомлённых майнкрафтеров"},
            {"role": Role.TERRARIA, "text": "команды для игроков террарии"},
        ]
        output = ""
        for role in ordered_roles:
            if self.event.sender.check_role(role['role']) and help_texts[role['role'].name]:
                output += f"\n\n— {role['text']} —\n"
                output += help_texts[role['role'].name]
        if help_texts['games']:
            output += "\n\n— игры —\n"
            output += help_texts['games']
        output = output.rstrip()
        return output
