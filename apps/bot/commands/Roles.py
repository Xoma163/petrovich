from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning


def get_roles(user):
    active_roles = []
    for group in user.groups.all():
        active_roles.append(Role[group.name].value)
    return active_roles


class Roles(Command):
    name = "роли"
    name_tg = 'roles'
    help_text = "присылает список ваших ролей"
    help_texts = [
        "- присылает ваши роли",
        "[N] - роли пользователя в беседе. N - имя, фамилия, логин/id, никнейм"
    ]

    def start(self):

        if self.event.message.args:
            self.check_conversation()
            try:
                user = self.bot.get_user_by_name(self.event.message.args, self.event.chat)
            except PWarning as e:
                return str(e)
        else:
            user = self.event.sender

        roles = get_roles(user)
        if len(roles) == 0:
            raise PWarning("Нет прав")

        result = "\n".join(roles)

        if self.event.chat and self.event.chat.admin == user:
            result += "\n" \
                      "админ конфы (в этой)"
        return result
