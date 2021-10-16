from django.contrib.auth.models import Group

from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand


class Ban(CommonCommand):
    name = "бан"
    help_text = "бан пользователя"
    help_texts = ["(N) - бан пользователя, где N - имя, фамилия, логин/id, никнейм"]
    access = Role.ADMIN
    args = 1
    excluded_platforms = [Platform.API, Platform.YANDEX]

    def start(self):
        user = self.bot.get_user_by_name(self.event.message.args, self.event.chat)

        if user.check_role(Role.ADMIN):
            raise PWarning("Нельзя банить админа")
        group_banned = Group.objects.get(name=Role.BANNED.name)
        user.groups.add(group_banned)
        user.save()

        return "Забанен"
