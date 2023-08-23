from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class Roles(Command):
    name = "роли"
    name_tg = 'roles'
    help_text = "присылает список ваших ролей"
    help_texts = [
        "- присылает ваши роли",
        "[N] - роли пользователя в беседе. N - имя, фамилия, логин/id, никнейм"
    ]

    def start(self) -> ResponseMessage:
        if not self.event.message.args:
            user = self.event.sender
        else:
            self.check_conversation()
            user = self.bot.get_profile_by_name(self.event.message.args, self.event.chat)

        roles = self.get_roles(user)
        if len(roles) == 0:
            raise PWarning("Нет прав")

        answer = "\n".join(roles)

        if self.event.chat and self.event.chat.admin == user:
            answer += "\nадмин конфы (в этой)"
        return ResponseMessage(ResponseMessageItem(text=answer))

    @staticmethod
    def get_roles(user):
        active_roles = []
        for group in user.groups.all():
            active_roles.append(Role[group.name].value)
        return active_roles
