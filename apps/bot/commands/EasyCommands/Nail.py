from apps.bot.classes.common.CommonCommand import CommonCommand


class Nail(CommonCommand):
    def __init__(self):
        names = ["наиль", "латыпов"]
        super().__init__(names, suggest_for_similar=False)

    def start(self):
        result = [
            "НАИЛЬ",
            "ЛАТЫПОВ",
            "МОЛОДЕЦ",
            "ПОЛИТИК ЛИДЕР И БОРЕЦ",
            "НАШ ЖИРОБАС МАКДАК ПОДНЯЛ",
            "И КФС ОН НЕ ПРЕДАЛ",
        ]
        return result
