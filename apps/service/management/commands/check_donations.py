import requests
from django.core.management.base import BaseCommand

from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.messages.ResponseMessage import ResponseMessageItem
from apps.bot.models import Chat
from apps.service.models import Service, Donations
from petrovich.settings import env

tg_bot = TgBot()


class Command(BaseCommand):

    def handle(self, *args, **options):
        url = "https://www.donationalerts.com/api/v1/alerts/donations"
        headers = {'Authorization': 'Bearer ' + env.str('DONATIONALERT_ACCESS_TOKEN')}
        r = requests.get(url, headers=headers).json()
        donations, created = Service.objects.get_or_create(name='donations')
        if created:
            donations.value = r['meta']['total']
            donations.save()
            return
        new_donation_count = int(r['meta']['total']) - int(donations.value)
        donations.value = r['meta']['total']
        donations.save()

        if new_donation_count > 0:
            if new_donation_count == 1:
                answer = 'Новый донат!\n\n'
            else:
                answer = 'Новые донаты!\n\n'
            for i in range(new_donation_count):
                donation = r['data'][i]
                new_donation = Donations(username=donation['username'],
                                         amount=donation['amount'],
                                         currency=donation['currency'],
                                         message=donation['message'])
                new_donation.save()
                answer += f"{donation['username']} - {donation['amount']} {donation['currency']}:\n" \
                          f"{donation['message']}\n\n"
            chat_pks = options['chat_id'][0].split(',')
            for chat_pk in chat_pks:
                chat = Chat.objects.get(pk=chat_pk)
                rmi = ResponseMessageItem(text=answer, peer_id=chat.chat_id)
                tg_bot.send_response_message_item(rmi)

    def add_arguments(self, parser):
        parser.add_argument('chat_id', nargs='+', type=str,
                            help='chat_id')
