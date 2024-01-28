from threading import Lock

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.utils import get_random_int
from apps.games.models import Rate as RateModel
from petrovich.settings import STATIC_ROOT

lock = Lock()


class Rates(Command):
    name = 'ставки'

    help_text = HelpText(
        commands_text="играет ставки",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(None, "играет ставки")
            ])
        ]
    )

    conversation = True
    platforms = [Platform.TG]

    bot: TgBot

    def start(self) -> ResponseMessage:
        with lock:
            min_gamers = 2

            gamers = RateModel.objects.filter(chat=self.event.chat).order_by("date")
            if len(gamers) < min_gamers:
                raise PWarning(f"Минимальное количество игроков - {min_gamers}")
            rmi1 = ResponseMessageItem("Ставки сделаны, ставок больше нет.")

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
                image = self.bot.get_photo_attachment(
                    f"{STATIC_ROOT}/bot/img/rate.jpg",
                    peer_id=self.event.peer_id,
                    filename="petrovich_rate.jpg"
                )
                if len(winners) == 1:
                    answer = f"Выпавшее число - {rnd}\nПобедитель этого казино:\n{winners_str}"
                else:
                    answer = f"Выпавшее число - {rnd}\nПобедители этого казино:\n{winners_str}"
                rmi2 = ResponseMessageItem(text=answer, attachments=[image])

            else:
                if len(winners) == 1:
                    answer = f"Выпавшее число - {rnd}\nПобедитель:\n{winners_str}"
                else:
                    answer = f"Выпавшее число - {rnd}\nПобедители:\n{winners_str}"
                rmi2 = ResponseMessageItem(text=answer)
            gamers.delete()

            button1 = self.bot.get_button("Ставка", "Ставка")
            keyboard = self.bot.get_inline_keyboard([button1], cols=1)
            rmi2.keyboard = keyboard
            return ResponseMessage([
                rmi1, rmi2
            ])
