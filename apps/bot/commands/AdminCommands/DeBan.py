from django.contrib.auth.models import Group

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform


class DeBan(Command):
    name = "разбан"
    help_text = "разбан пользователя"
    help_texts = ["(N) - разбан пользователя, где N - имя, фамилия, логин/id, никнейм"]
    access = Role.ADMIN
    args = 1
    excluded_platforms = [Platform.API, Platform.YANDEX]

    def start(self):
        user = self.bot.get_user_by_name(self.event.message.args, self.event.chat)
        group_banned = Group.objects.get(name=Role.BANNED.name)
        user.groups.remove(group_banned)
        user.save()
        return "Разбанен"
