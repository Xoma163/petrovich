from threading import Lock

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import random_event
from apps.games.models import Rate as RateModel

lock = Lock()


class Rate(Command):
    name = "ставка"
    name_tg = 'rate'

    help_text = "игра, определяющая, кто ближе угадал загаданное число"
    help_texts = ["[ставка=рандом] - делает ставку"]
    help_texts_extra = "Ставка может быть от 1 до 100"

    int_args = [0]
    conversation = True
    platforms = [Platform.TG]
    access = Role.GAMER

    def start(self):
        with lock:
            gamer = self.bot.get_gamer_by_profile(self.event.sender)

            # min_gamers = int(len(Profile.objects.filter(chats=self.event.chat)) / 3)
            # if min_gamers < 2:
            min_gamers = 2
            rates_gamers = RateModel.objects.filter(chat=self.event.chat)
            existed_rate = rates_gamers.filter(gamer=gamer)

            rate_gamer_str = ""
            for rate_gamer in rates_gamers:
                if rate_gamer.random:
                    rate_gamer_str += f"{str(rate_gamer.gamer)} - {rate_gamer.rate} (R)\n"
                else:
                    rate_gamer_str += f"{str(rate_gamer.gamer)} - {rate_gamer.rate}\n"

            if len(existed_rate) > 0:
                raise PWarning(
                    f"Ставка уже поставлена\n"
                    f"Игроки {rates_gamers.count()}/{min_gamers}:\n"
                    f"{rate_gamer_str}",
                    reply_to=self.event.message.id)
            if self.event.message.args:
                random = False
                arg = self.event.message.args[0]
                self.check_number_arg_range(arg, 1, 100)
            else:
                random = True
                available_list = [x for x in range(1, 101)]
                rates = RateModel.objects.filter(chat=self.event.chat)
                for rate_entity in rates:
                    available_list.pop(available_list.index(rate_entity.rate))
                if len(available_list) == 0:
                    raise PWarning(
                        "Какая-то жесть, 100 игроков в ставке, я не могу больше придумать чисел, играйте((")
                arg = random_event(available_list)

            existed_another_rate = RateModel.objects.filter(chat=self.event.chat, rate=arg)
            if len(existed_another_rate) > 0:
                raise PWarning("Эта ставка уже поставлена другим игроком")

            RateModel(
                **{'gamer': gamer, 'chat': self.event.chat, 'rate': arg, 'random': random}).save()
            if random:
                rate_gamer_str += f"{gamer} - {arg} (R)\n"
            else:
                rate_gamer_str += f"{gamer} - {arg}\n"

            buttons = [self.bot.get_button("Ставка", self.name)]
            if rates_gamers.count() + 1 >= min_gamers:
                buttons.append(self.bot.get_button("Ставки", "Ставки"))
            keyboard = self.bot.get_inline_keyboard(buttons, cols=2)
            text = f"Игроки {rates_gamers.count() + 1}/{min_gamers}:\n" \
                   f"{rate_gamer_str}"
            return {
                'text': text,
                'keyboard': keyboard,
            }
