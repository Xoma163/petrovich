from django.contrib.auth.models import Group

from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class DeBan(CommonCommand):
    names = ["разбан", "дебан"]
    help_text = "Разбан - разбан пользователя"
    detail_help_text = "Разбан (N) - разбан пользователя, где N - имя, фамилия, логин/id, никнейм"
    access = Role.ADMIN
    args = 1

    def start(self):
        user = self.bot.get_user_by_name(self.event.args, self.event.chat)
        group_banned = Group.objects.get(name=Role.BANNED.name)
        user.groups.remove(group_banned)
        user.save()
        return "Разбанен"
