from threading import Lock

from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_random_int
from apps.games.models import Rate as RateModel
from petrovich.settings import STATIC_DIR

lock = Lock()


class Rates(CommonCommand):
    names = ["ставки", "казино"]
    help_text = "Ставки - играет ставки"
    detail_help_text = "Ставки - играет ставки.\n\n" \
                       "Ставки f - играет независимо от количества игроков. Только для админов конфы"
    conversation = True
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        with lock:
            min_gamers = int(len(self.bot.user_model.filter(chats=self.event.chat)) / 2)
            if min_gamers < 2:
                min_gamers = 2

            gamers = RateModel.objects.filter(chat=self.event.chat).order_by("date")
            if self.event.args and self.event.args[0] == 'f':
                self.check_sender(Role.CONFERENCE_ADMIN)
                if len(gamers) <= 1:
                    raise PWarning("Ну ты ваще обалдел? Хотя бы один игрок-то пусть будет")
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

            if self.event.command == "казино":
                attachments = self.bot.upload_photos(f"{STATIC_DIR}/bot/img/rate.jpg")
                if len(winners) == 1:
                    msg = {'msg': f"Выпавшее число - {rnd}\nПобедитель этого казино:\n{winners_str}",
                           'attachments': attachments}
                else:
                    msg = {'msg': f"Выпавшее число - {rnd}\nПобедители этого казино:\n{winners_str}",
                           'attachments': attachments}
            else:
                if len(winners) == 1:
                    msg = f"Выпавшее число - {rnd}\nПобедитель:\n{winners_str}"
                else:
                    msg = f"Выпавшее число - {rnd}\nПобедители:\n{winners_str}"

            gamers.delete()
            messages.append(msg)
            return messages
