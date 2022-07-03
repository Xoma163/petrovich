from threading import Lock

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.models import Profile
from apps.bot.utils.utils import get_random_int
from apps.games.models import Rate as RateModel
from petrovich.settings import STATIC_ROOT

lock = Lock()


class Rates(Command):
    name = 'ставки'
    name_tg = 'rates'

    help_text = "играет ставки"
    help_texts = [
        "- играет ставки",
        "f - играет независимо от количества игроков. Только для админов конфы"
    ]

    conversation = True
    platforms = [Platform.VK, Platform.TG]
    access = Role.GAMER

    def start(self):
        with lock:
            min_gamers = int(len(Profile.objects.filter(chats=self.event.chat)) / 3)
            if min_gamers < 2:
                min_gamers = 2

            gamers = RateModel.objects.filter(chat=self.event.chat).order_by("date")
            if self.event.message.args and self.event.message.args[0] == 'f':
                self.check_sender(Role.CONFERENCE_ADMIN)
                if len(gamers) < 2:
                    raise PWarning("Ну ты ваще обалдел? Хотя бы два игрока-то пусть будет")
            else:
                if len(gamers) < min_gamers:
                    raise PWarning(f"Минимальное количество игроков - {min_gamers}")
            messages = ["Ставки сделаны, ставок больше нет."]

            rnd = get_random_int(1, 100)

            winner_rates = ([abs(rnd - gamer.rate) for gamer in gamers])
            min_val = min(winner_rates)
            winners = []
            for i, winner_rate in enumerate(winner_rates):
                if winner_rate == min_val:
                    winners.append(gamers[i])

            winners_str = ""
            for winner in winners:
                gamer = winner.gamer
                winners_str += f"{gamer}\n"

                if winner.rate != rnd:
                    gamer.points += 1
                else:
                    gamer.points += 5
                    winners_str += "\nБонус x5 за точное попадание\n"

                gamer.save()

            if self.event.message.command == "казино":
                image = self.bot.upload_photo(f"{STATIC_ROOT}/bot/img/rate.jpg", peer_id=self.event.peer_id)
                if len(winners) == 1:
                    msg = {'text': f"Выпавшее число - {rnd}\nПобедитель этого казино:\n{winners_str}",
                           'attachments': image}
                else:
                    msg = {'text': f"Выпавшее число - {rnd}\nПобедители этого казино:\n{winners_str}",
                           'attachments': image}
            else:
                if len(winners) == 1:
                    msg = {'text': f"Выпавшее число - {rnd}\nПобедитель:\n{winners_str}"}
                else:
                    msg = {'text': f"Выпавшее число - {rnd}\nПобедители:\n{winners_str}"}

            gamers.delete()
            messages.append(msg)

            button1 = self.bot.get_button("Ставка", "Ставка")
            button2 = self.bot.get_button("Ставки", self.name)
            keyboard = self.bot.get_inline_keyboard([button1, button2])

            if 'callback_query' in self.event.raw:
                message_id = self.event.raw['callback_query']['message']['message_id']
            else:
                message_id = None

            messages[-1]['keyboard'] = keyboard
            messages[-1]['message_id'] = message_id

            return messages
