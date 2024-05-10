from threading import Lock

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.commands.game.rates import Rates
from apps.bot.utils.utils import random_event
from apps.games.models import Rate as RateModel

lock = Lock()


class Rate(Command):
    name = "ставка"

    help_text = HelpText(
        commands_text="игра, определяющая, кто ближе угадал загаданное число",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("[ставка=рандом]", "делает ставку")
            ])
        ],
        extra_text=(
            "Ставка может быть от 1 до 100"
        )
    )

    int_args = [0]
    conversation = True
    platforms = [Platform.TG]

    bot: TgBot

    MIN_GAMERS = Rates.MIN_GAMERS

    def start(self) -> ResponseMessage:
        with lock:
            rates = RateModel.objects.filter(chat=self.event.chat)
            existed_rate = rates.filter(gamer=self.event.sender.gamer)
            if len(existed_rate) > 0:
                rates_str = self._get_rates_gamer_str(rates)
                warning_msg = f"Ставка уже поставлена\n" \
                              f"Игроки {rates.count()}/{self.MIN_GAMERS}:\n" \
                              f"{rates_str}"
                raise PWarning(warning_msg, reply_to=self.event.message.id)

            new_rate = self.create_new_rate(rates)
            rates_str = self._get_rate_gamer_str(new_rate)

            buttons = [self.bot.get_button("Ставка", self.name)]
            if rates.count() + 1 >= self.MIN_GAMERS:
                command_name = Rates.name.capitalize()
                rates_button = self.bot.get_button(command_name, command_name)
                buttons.append(rates_button)
            keyboard = self.bot.get_inline_keyboard(buttons, cols=2)

            answer = f"Игроки {rates.count() + 1}/{self.MIN_GAMERS}:\n" \
                     f"{rates_str}"

            return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard))

    def create_new_rate(self, rates_gamers) -> RateModel:
        if self.event.message.args:
            random = False
            new_rate = self.event.message.args[0]
            self.check_number_arg_range(new_rate, 1, 100)
        else:
            random = True
            _rates = [rate_gamer.rate for rate_gamer in rates_gamers]
            available_list = [x for x in range(1, 101) if x not in _rates]
            if len(available_list) == 0:
                raise PWarning("Какая-то жесть, 100 игроков в ставке, я не могу больше придумать чисел, играйте((")
            new_rate = random_event(available_list)

        new_rate_gamer = RateModel(
            gamer=self.event.sender.gamer,
            chat=self.event.chat,
            rate=new_rate,
            random=random
        )
        new_rate_gamer.save()

        return new_rate_gamer

    def _get_rates_gamer_str(self, rates_gamers):
        rate_gamers = [self._get_rate_gamer_str(rate_gamer) for rate_gamer in rates_gamers]
        return "\n".join(rate_gamers)

    @staticmethod
    def _get_rate_gamer_str(rate_gamer):
        if rate_gamer.random:
            return f"{str(rate_gamer.gamer)} - {rate_gamer.rate} (R)"
        else:
            return f"{str(rate_gamer.gamer)} - {rate_gamer.rate}"
