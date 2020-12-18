from apps.bot.classes.common.CommonCommand import CommonCommand


class Nail(CommonCommand):
    def __init__(self):
        names = ["арман", "розенков"]
        super().__init__(names, suggest_for_similar=False)

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
