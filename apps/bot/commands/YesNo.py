from apps.bot.classes.Consts import BAD_ANSWERS
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_random_int, random_event, replace_similar_letters


def get_bad_words():
    return ['еба', 'пидор', 'пидар', "пидр", 'гандон', 'гондон', 'хуй', 'пизд', 'бля', 'шлюха', 'мудак', 'говно',
            'моча', 'залупа', 'гей', 'дурак', 'говно', 'жопа', 'ублюдок', 'мудак', 'сука']


class YesNo(CommonCommand):
    name = "?"
    help_text = "вернёт да или нет"
    help_texts = ["- вернёт да или нет. Для вызова команды просто в конце нужно написать знак вопроса"]
    priority = 80

    def accept(self, event):
        if event.message.clear and event.message.clear[-1] == self.name:
            return True
        return super().accept(event)

    def start(self):
        clear = replace_similar_letters(self.event.message.clear)
        if clear.lower() in ['идиот?', 'ты идиот?']:
            return "Мне потанцевать нельзя?"
        elif clear.lower() in ['да?']:
            return {'attachments': 'video162408856_456239566'}

        bad_words = get_bad_words()

        # if not self.event.sender.check_role(Role.ADMIN):
        min_index_bad = len(clear)
        max_index_bad = -1
        for word in bad_words:
            ind = clear.lower().find(word)
            if ind != -1:
                if ind < min_index_bad:
                    min_index_bad = ind
                if ind > max_index_bad:
                    max_index_bad = ind

        min_index_bad = clear.rfind(' ', 0, min_index_bad)
        if min_index_bad == -1:
            min_index_bad = clear.rfind(',', 0, min_index_bad)
            if min_index_bad == -1:
                min_index_bad = clear.rfind('.', 0, min_index_bad)
                if min_index_bad == -1:
                    min_index_bad = clear.find('/')
        min_index_bad += 1
        if max_index_bad != -1:
            len_bad = clear.find(',', max_index_bad)
            if len_bad == -1:
                len_bad = clear.find(' ', max_index_bad)
                if len_bad == -1:
                    len_bad = clear.find('?', max_index_bad)
                    if len_bad == -1:
                        len_bad = len(clear)

            rand_int = get_random_int(len(BAD_ANSWERS) - 1)
            messages = [BAD_ANSWERS[rand_int]]
            name = self.event.sender.name
            if self.event.sender.gender == '1':
                msg_self = "сама"
            else:
                msg_self = "сам"
            messages.append(f"{name}, может ты {msg_self} {clear[min_index_bad: len_bad]}?")
            return messages

        random_events = [["Да", "Ага", "Канеш", "Само собой", "Абсолютно"],
                         ["Нет", "Неа", "Ни за что", "Нуу... нет", "NO"],
                         ["Ну тут даже я хз", "ДА НЕ ЗНАЮ Я", "Хз", "Спроси у другого бота", "Да нет наверное"]]
        probability_events1 = [47, 47, 6]
        probability_events2 = [40, 15, 15, 15, 15]
        seed = clear
        selected_event = random_event(random_events, probability_events1, seed=seed)
        selected_event2 = random_event(selected_event, probability_events2, seed=seed)
        return selected_event2
