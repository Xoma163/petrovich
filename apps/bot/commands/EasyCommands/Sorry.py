from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import random_event

sorry_phrases = ["лан", "нет", "окей", "ничего страшного", "Петрович любит тебя", "я подумаю", "ой всё",
                 "ну а чё ты :(", "всё хорошо", "каво", "сь", '...', 'оке', 'ладно, но больше так не делай']


class Sorry(CommonCommand):
    name = 'сори'
    names = ['прости', 'извини', 'простите', 'извините', 'извиняюсь']

    def start(self):
        return random_event(sorry_phrases)
