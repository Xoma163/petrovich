from apps.bot.classes.Command import Command
from apps.bot.utils.utils import random_event, replace_similar_letters


class YesNo(Command):
    name = "?"
    help_text = "вернёт да или нет"
    help_texts = ["- вернёт да или нет"]
    help_texts_extra = "Для вызова команды просто в конце нужно написать знак вопроса"
    priority = -10
    mentioned = True

    def accept(self, event):
        if event.message and event.message.clear and event.message.clear[-1] == self.name:
            return True
        return super().accept(event)

    def start(self):
        clear = replace_similar_letters(self.event.message.clear)
        if clear in ['идиот?', 'ты идиот?']:
            return "Мне потанцевать нельзя?"
        elif clear in ['да?']:
            return "https://youtu.be/ePddSQQl2kc"

        random_events = [["Да", "Ага", "Канеш", "Само собой", "Абсолютно"],
                         ["Нет", "Неа", "Ни за что", "Нуу... нет", "NO"],
                         ["Ну тут даже я хз", "ДА НЕ ЗНАЮ Я", "Хз", "Спроси у другого бота", "Да нет наверное"]]
        probability_events1 = [45, 45, 10]
        probability_events2 = [25, 19, 19, 19, 19]
        seed = clear
        selected_event = random_event(random_events, probability_events1, seed=seed)
        selected_event2 = random_event(selected_event, probability_events2, seed=seed)
        return selected_event2
