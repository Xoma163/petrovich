from django.core.management import BaseCommand

from apps.birds.CameraHandler import CameraHandler
from apps.bot.models import Profile, User

camera_handler = CameraHandler()


class Command(BaseCommand):

    def handle(self, *args, **options):
        all_profiles = Profile.objects.all()
        for profile in all_profiles:
            User.objects.get_or_create(user_id=profile.user_id, platform=profile.platform,
                                       profile=profile, nickname=profile.nickname)
