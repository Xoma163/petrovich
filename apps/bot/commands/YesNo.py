from apps.bot.classes.Consts import Role, BAD_ANSWERS
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import get_random_int, random_event


def get_bad_words():
    return ['еба', 'ебa', 'eба', 'eбa', 'ёба', 'ёбa', 'пидор', 'пидoр', 'пидоp', 'пидop', 'пидар', 'пидaр',
            'пидаp', 'пидap', "пидр", "пидp", 'гандон', 'годнон', 'хуй', 'пизд', 'бля', 'шлюха', 'мудак',
            'говно', 'моча', 'залупа', 'гей', 'дурак', 'говно', 'жопа', 'ублюдок', 'мудак',
            'сука', 'сукa', 'сyка', 'сyкa', 'cука', 'cукa', 'cyка', 'cyкa', 'суkа', 'суka', 'сykа', 'сyka', 'cуkа',
            'cуka', 'cykа', 'cyka']


class YesNo(CommonCommand):
    def __init__(self):
        names = ["вопрос", "?"]
        help_text = "...? - вернёт да или нет"
        detail_help_text = "...? - вернёт да или нет. Для вызова команды просто в конце нужно написать знак вопроса"
        super().__init__(names, help_text, detail_help_text, priority=80)

    def accept(self, event):
        if (event.msg and event.msg[-1] == '?') or event.command in self.names:
            return True
        return False

    def start(self):
        if self.event.msg.lower() in ['идиот?', 'ты идиот?']:
            return "Мне потанцевать нельзя?"
        elif self.event.msg.lower() in ['да?']:
            return {'attachments': 'video162408856_456239566'}

        bad_words = get_bad_words()

        if not self.event.sender.check_role(Role.ADMIN):
            min_index_bad = len(self.event.msg)
            max_index_bad = -1
            for word in bad_words:
                ind = self.event.msg.lower().find(word)
                if ind != -1:
                    if ind < min_index_bad:
                        min_index_bad = ind
                    if ind > max_index_bad:
                        max_index_bad = ind

            min_index_bad = self.event.msg.rfind(' ', 0, min_index_bad)
            if min_index_bad == -1:
                min_index_bad = self.event.msg.rfind(',', 0, min_index_bad)
                if min_index_bad == -1:
                    min_index_bad = self.event.msg.rfind('.', 0, min_index_bad)
                    if min_index_bad == -1:
                        min_index_bad = self.event.msg.find('/')
            min_index_bad += 1
            if max_index_bad != -1:
                len_bad = self.event.msg.find(',', max_index_bad)
                if len_bad == -1:
                    len_bad = self.event.msg.find(' ', max_index_bad)
                    if len_bad == -1:
                        len_bad = self.event.msg.find('?', max_index_bad)
                        if len_bad == -1:
                            len_bad = len(self.event.msg)

                rand_int = get_random_int(len(BAD_ANSWERS) - 1)
                messages = [BAD_ANSWERS[rand_int]]
                name = self.event.sender.name
                if self.event.sender.gender == '1':
                    msg_self = "сама"
                else:
                    msg_self = "сам"
                messages.append(f"{name}, может ты {msg_self} {self.event.msg[min_index_bad: len_bad]}?")
                return messages

        random_events = [["Да", "Ага", "Канеш", "Само собой", "Абсолютно"],
                         ["Нет", "Неа", "Ни за что", "Невозможно", "NO"],
                         ["Ну тут даже я хз", "ДА НЕ ЗНАЮ Я", "Хз", "Спроси у другого бота", "Да нет наверное"]]
        probability_events1 = [47, 47, 6]
        probability_events2 = [40, 15, 15, 15, 15]
        selected_event = random_event(random_events, probability_events1)
        selected_event2 = random_event(selected_event, probability_events2)
        return selected_event2
