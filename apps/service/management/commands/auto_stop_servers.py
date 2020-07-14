from django.core.management.base import BaseCommand

from apps.bot.APIs.Minecraft import servers_minecraft


class Command(BaseCommand):

    def handle(self, *args, **options):
        for server in servers_minecraft:
            server.stop_if_need()
