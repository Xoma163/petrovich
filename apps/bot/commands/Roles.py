from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning


class Roles(Command):
    name = "роли"
    name_tg = 'roles'
    help_text = "присылает список ваших ролей"
    help_texts = [
        "- присылает ваши роли",
        "[N] - роли пользователя в беседе. N - имя, фамилия, логин/id, никнейм"
    ]

    def start(self):
        if not self.event.message.args:
            user = self.event.sender
        else:
            self.check_conversation()
            try:
                user = self.bot.get_profile_by_name(self.event.message.args, self.event.chat)
            except PWarning as e:
                return str(e)

        roles = self.get_roles(user)
        if len(roles) == 0:
            raise PWarning("Нет прав")

        result = "\n".join(roles)

        if self.event.chat and self.event.chat.admin == user:
            result += "\nадмин конфы (в этой)"
        return result

    @staticmethod
    def get_roles(user):
        active_roles = []
        for group in user.groups.all():
            active_roles.append(Role[group.name].value)
        return active_roles
