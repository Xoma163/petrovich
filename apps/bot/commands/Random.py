from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_random_int


class Random(CommonCommand):
    name = "рандом"
    names = ["ранд", 'р', 'p']
    help_text = "рандомное число в заданном диапазоне"
    help_texts = [
        "- рандомное число в диапазоне[0:1]",
        "N - рандомное число в заданном диапазоне[1:N]",
        "N,M - рандомное число в заданном диапазоне[N:M]"
    ]
    int_args = [0, 1]

    def start(self):
        if self.event.message.args:
            if len(self.event.message.args) == 2:
                int1 = self.event.message.args[0]
                int2 = self.event.message.args[1]
            else:
                int1 = 1
                int2 = self.event.message.args[0]
                self.check_number_arg_range(int2, 2)
        else:
            int1 = 0
            int2 = 1

        if int1 > int2:
            int1, int2 = int2, int1

        rand_int = get_random_int(int1, int2)
        return str(rand_int)
