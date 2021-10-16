from apps.bot.classes.Command import Command
from apps.bot.utils.utils import random_event


class Bye(Command):
    name = "пока"
    names = ["бай", "bb", "бай-бай", "байбай", "бб", "досвидос", "до встречи", "бывай", 'пока-пока', 'пока((']

    def start(self):
        return random_event(self.full_names)
