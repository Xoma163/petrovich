from django.core.management.base import BaseCommand

from apps.bot.APIs.Minecraft import minecraft_servers


class Command(BaseCommand):

    def handle(self, *args, **options):
        for server in minecraft_servers:
            server.stop_if_need()
