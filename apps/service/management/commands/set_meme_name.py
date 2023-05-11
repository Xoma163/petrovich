from django.core.management import BaseCommand

from apps.service.models import Meme


class Command(BaseCommand):
    for meme in Meme.objects.all():
        meme.name = meme.name.lower()
        meme.save()
