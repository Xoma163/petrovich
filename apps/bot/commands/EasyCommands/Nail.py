from apps.bot.classes.common.CommonCommand import CommonCommand


class Nail(CommonCommand):
    names = ["наиль", "латыпов"]
    suggest_for_similar = False

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
