from threading import Lock

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.utils import get_random_int
from apps.games.models import Rate as RateModel

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

    MIN_GAMERS = 2

    def start(self) -> ResponseMessage:
        with lock:
            rates = RateModel.objects.filter(chat=self.event.chat).order_by("date")
            if rates.count() < self.MIN_GAMERS:
                raise PWarning(f"Минимальное количество игроков - {self.MIN_GAMERS}")

            answer = "Ставки сделаны, ставок больше нет."
            rmi1 = ResponseMessageItem(answer)

            random_int = get_random_int(1, 100)
            winners = self._get_winners(rates, random_int)
            winners_str = self._get_winners_str(winners, random_int)

            _winners_plural = "Победители" if len(winners) > 1 else "Победитель"
            answer = f"Выпавшее число - {random_int}\n{_winners_plural}:\n{winners_str}"
            button = self.bot.get_button("Ставка", "Ставка")
            keyboard = self.bot.get_inline_keyboard([button], cols=1)
            rmi2 = ResponseMessageItem(text=answer, keyboard=keyboard)
            rates.delete()

            return ResponseMessage([rmi1, rmi2])

    @staticmethod
    def _get_winners(rates, random_int):
        winner_rates = ([abs(random_int - gamer.rate) for gamer in rates])
        min_val = min(winner_rates)
        winners = []
        for i, winner_rate in enumerate(winner_rates):
            if winner_rate == min_val:
                winners.append(rates[i])

        for winner in winners:
            gamer = winner.gamer
            if winner.rate != random_int:
                gamer.points += 1
            else:
                gamer.points += 5

            gamer.points += 1
            gamer.save()
        return winners

    @staticmethod
    def _get_winners_str(winners, random_int):
        _answer = []
        for winner in winners:
            gamer = winner.gamer
            _answer.append(str(gamer))
            if winner.rate == random_int:
                _answer.append("\nБонус x5 за точное попадание\n")
        return "\n".join(_answer)
