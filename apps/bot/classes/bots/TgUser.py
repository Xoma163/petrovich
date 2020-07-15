from telethon import TelegramClient

from petrovich.settings import env


class TgUser:
    def __init__(self):
        super().__init__()
        tg_client = TelegramClient('session_name', env('TG_APP_API_ID'), env('TG_APP_API_HASH'))
        tg_client.start()
        tg_client.get_me()

    @staticmethod
    def auth_handler():
        key = input("Enter authentication code: ")
        remember_device = True
        return key, remember_device
