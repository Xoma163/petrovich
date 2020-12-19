from apps.bot.classes.Consts import Role
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand


def get_roles(user):
    active_roles = []
    for group in user.groups.all():
        active_roles.append(Role[group.name].value)
    return active_roles


class Roles(CommonCommand):
    def __init__(self):
        names = ["роли"]
        help_text = "Роли - присылает список ваших ролей"
        detail_help_text = "Роли - присылает ваши роли\n" \
                           "Роли [N] - роли пользователя в беседе. N - имя, фамилия, логин/id, никнейм"

        super().__init__(names, help_text, detail_help_text)

    def start(self):

        if self.event.args:
            self.check_conversation()
            try:
                user = self.bot.get_user_by_name(self.event.args, self.event.chat)
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
