import requests
from django.core.management.base import BaseCommand

from apps.bot.classes.bots.VkBot import VkBot
from apps.bot.models import Chat
from apps.service.models import Service, Donations
from petrovich.settings import env

vk_bot = VkBot()


class Command(BaseCommand):

    def handle(self, *args, **options):
        URL = f"https://www.donationalerts.com/api/v1/alerts/donations"
        headers = {'Authorization': 'Bearer ' + env.str('DONATIONALERT_ACCESS_TOKEN')}
        response = requests.get(URL, headers=headers).json()
        donations, created = Service.objects.get_or_create(name='donations')
        if created:
            donations.value = response['meta']['total']
            donations.save()
            return
        new_donation_count = int(response['meta']['total']) - int(donations.value)
        donations.value = response['meta']['total']
        donations.save()

        if new_donation_count > 0:
            if new_donation_count == 1:
                result_str = 'Новый донат!\n\n'
            else:
                result_str = 'Новые донаты!\n\n'
            for i in range(new_donation_count):
                donation = response['data'][i]
                new_donation = Donations(username=donation['username'],
                                         amount=donation['amount'],
                                         currency=donation['currency'],
                                         message=donation['message'])
                new_donation.save()
                result_str += f"{donation['username']} - {donation['amount']} {donation['currency']}:\n" \
                              f"{donation['message']}\n\n"
            chat_ids = options['chat_id'][0].split(',')
            for chat_id in chat_ids:
                chat = Chat.objects.filter(chat_id=vk_bot.get_group_id(chat_id))

                if not chat:
                    print(f"Чата с id = {chat_id} не существует")
                    break
                chat = chat.first()
                vk_bot.send_message(chat.chat_id, result_str)

    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str,
                            help='chat_id')
