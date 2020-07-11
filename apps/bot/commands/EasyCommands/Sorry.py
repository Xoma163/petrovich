from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import random_event

sorry_phrases = ["лан", "нет", "окей", "ничего страшного", "Петрович любит тебя", "я подумаю", "ой всё",
                 "ну а чё ты :(", "всё хорошо", "каво", "сь", '...', 'оке', 'ладно, но больше так не делай']


class Sorry(CommonCommand):
    def __init__(self):
        names = ['сори', 'прости', 'извини', 'простите', 'извините', 'извиняюсь']
        super().__init__(names)

    def start(self):
        return random_event(sorry_phrases)
