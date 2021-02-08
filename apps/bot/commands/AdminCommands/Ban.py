from django.contrib.auth.models import Group

from apps.bot.classes.Consts import Role
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand


class Ban(CommonCommand):
    names = ["бан"]
    help_text = "Бан - бан пользователя"
    detail_help_text = "Бан (N) - бан пользователя, где N - имя, фамилия, логин/id, никнейм"
    access = Role.ADMIN
    args = 1

    def start(self):
        user = self.bot.get_user_by_name(self.event.args, self.event.chat)

        if user.check_role(Role.ADMIN):
            raise PWarning("Нельзя банить админа")
        group_banned = Group.objects.get(name=Role.BANNED.name)
        user.groups.add(group_banned)
        user.save()

        return "Забанен"
