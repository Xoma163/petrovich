from apps.bot.classes.Command import Command
from apps.bot.classes.events.Event import Event


class No(Command):
    name = "нет"
    args = 0
    suggest_for_similar = False
    non_mentioned = True

    def accept(self, event: Event):
        if event.message and len(event.message.args) == 0:
            return super().accept(event)

    def start(self):
        return "Пидора ответ"
