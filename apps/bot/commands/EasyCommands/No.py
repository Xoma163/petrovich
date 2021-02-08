from apps.bot.classes.common.CommonCommand import CommonCommand


class No(CommonCommand):
    names = ["нет"]
    suggest_for_similar = False

    def start(self):
        return "Пидора ответ"
