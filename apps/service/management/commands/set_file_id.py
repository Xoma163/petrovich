from django.core.management import BaseCommand

from apps.service.models import Meme as MemeModel


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    def handle(self, *args, **kwargs):
        for meme in MemeModel.objects.filter(type='link', link__icontains="youtu", tg_file_id=''):
            meme.type = 'link'
            meme.save()
