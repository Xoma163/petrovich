from django.core.management import BaseCommand

from apps.bot.models import User


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        vk_users = User.objects.filter(platform="VK")
        tg_users = User.objects.filter(platform="TG")

        for user in vk_users:
            user.profile.default_platform = user.platform
            user.profile.save()

        for user in tg_users:
            user.profile.default_platform = user.platform
            user.profile.save()
