from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import random_event


class Bye(CommonCommand):
    name = "пока"
    names = ["бай", "bb", "бай-бай", "байбай", "бб", "досвидос", "до встречи", "бывай", 'пока-пока', 'пока((']
    suggest_for_similar = False

    def start(self):
        return random_event(self.all_names)
