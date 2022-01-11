from apps.bot.classes.Command import Command
from apps.bot.utils.utils import random_event


class Sorry(Command):
    name = 'сори'
    names = ['прости', 'извини', 'простите', 'извините', 'извиняюсь']
    suggest_for_similar = False
    non_mentioned = True

    def start(self):
        sorry_phrases = ["лан", "нет", "окей", "ничего страшного", "Петрович любит тебя", "я подумаю", "ой всё",
                         "ну а чё ты :(", "всё хорошо", "каво", "сь", '...', 'оке', 'ладно, но больше так не делай']
        return random_event(sorry_phrases)
