from threading import Lock

from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import random_event
from apps.games.models import Rate as RateModel

lock = Lock()


class Rate(CommonCommand):
    def __init__(self):
        names = ["ставка"]
        help_text = "Ставка - игра, определяющая, кто ближе угадал загаданное число"
        detail_help_text = "Ставка [ставка=рандом] - делает ставку"
        super().__init__(names, help_text, detail_help_text, int_args=[0], conversation=True, platforms=['vk', 'tg'])

    def start(self):
        with lock:
            gamer = self.bot.get_gamer_by_user(self.event.sender)

            min_gamers = int(len(self.bot.user_model.filter(chats=self.event.chat)) / 2)
            if min_gamers < 2:
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
                return f"Ставка уже поставлена\n" \
                       f"Игроки {len(rates_gamers)}/{min_gamers}:\n" \
                       f"{rate_gamer_str}"
            if self.event.args:
                random = False
                arg = self.event.args[0]
                self.check_number_arg_range(arg, 1, 100)
            else:
                random = True
                available_list = [x for x in range(1, 101)]
                rates = RateModel.objects.filter(chat=self.event.chat)
                for rate_entity in rates:
                    available_list.pop(available_list.index(rate_entity.rate))
                if len(available_list) == 0:
                    return "Какая-то жесть, 100 игроков в ставке, я не могу больше придумать чисел, играйте(("
                arg = random_event(available_list)

            existed_another_rate = RateModel.objects.filter(chat=self.event.chat, rate=arg)
            if len(existed_another_rate) > 0:
                return "Эта ставка уже поставлена другим игроком"

            RateModel(
                **{'gamer': gamer, 'chat': self.event.chat, 'rate': arg, 'random': random}).save()
            if random:
                rate_gamer_str += f"{gamer} - {arg} (R)\n"
            else:
                rate_gamer_str += f"{gamer} - {arg}\n"

            return f"Игроки {len(rates_gamers) + 1}/{min_gamers}:\n" \
                   f"{rate_gamer_str}"
