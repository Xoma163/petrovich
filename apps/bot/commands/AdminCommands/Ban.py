from django.contrib.auth.models import Group

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem


class Ban(Command):
    name = "бан"
    help_text = "бан пользователя"
    help_texts = ["(N) - бан пользователя, где N - имя, фамилия, логин/id, никнейм"]
    access = Role.ADMIN
    args = 1

    def start(self):
        profile = self.bot.get_profile_by_name(self.event.message.args, self.event.chat)

        if profile.check_role(Role.ADMIN):
            raise PWarning("Нельзя банить админа")
        group_banned = Group.objects.get(name=Role.BANNED.name)
        profile.groups.add(group_banned)
        profile.save()

        if profile.gender == profile.GENDER_FEMALE:
            answer = "Забанена"
        else:
            answer = "Забанен"

        return ResponseMessage(
            ResponseMessageItem(
                text=answer,
                peer_id=self.event.peer_id,
                message_thread_id=self.event.message_thread_id
            )
        )
