from apps.bot.classes.common.CommonCommand import CommonCommand


class Nail(CommonCommand):
    names = ["арман", "розенков"]
    suggest_for_similar = False

    def start(self):
        result = [
            "АРМАН",
            "РОЗЕНКОВ",
            "МОЛОДЕЦ",
            "ПОЛИТИК ЛИДЕР И БОРЕЦ",
            "АРМАН НАШ МЕМЫ ДОСТАВЛЯЛ",
            "И СТАТУ ОН СЕБЕ ПОДНЯЛ",
        ]
        return result
