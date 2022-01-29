from django.contrib.auth.models import Group

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role


class DeBan(Command):
    name = "разбан"
    help_text = "разбан пользователя"
    help_texts = ["(N) - разбан пользователя, где N - имя, фамилия, логин/id, никнейм"]
    access = Role.ADMIN
    args = 1

    def start(self):
        profile = self.bot.get_profile_by_name(self.event.message.args, self.event.chat)
        group_banned = Group.objects.get(name=Role.BANNED.name)
        profile.groups.remove(group_banned)
        profile.save()

        if profile.gender == profile.GENDER_FEMALE:
            return "Разбанена"
        return "Разбанен"
