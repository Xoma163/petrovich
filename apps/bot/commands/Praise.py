from apps.bot.classes.Consts import BAD_ANSWERS
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import random_event
from apps.service.models import Words

gender_translator = {
    'м': 'm1',
    'ж': 'f1',
    'с': 'n1',
    'м1': 'm1',
    'ж1': 'f1',
    'с1': 'n1',
    'мм': 'mm',
    'см': 'mm',
    'жм': 'fm'
}


def get_from_db(field_name, _type):
    my_field = {field_name + "__isnull": False, 'type': _type}
    try:
        word = getattr(Words.objects.filter(**my_field).order_by('?').first(), field_name).lower()
    except AttributeError:
        raise RuntimeWarning("Нет такого слова :(")
    except Exception as e:
        raise RuntimeWarning("Нет такого слова :(\n"
                             f"Ошибка - {str(e)}")
    return word


def add_phrase_before(recipient, word, field_name):
    if field_name[1] == '1':
        return f"{recipient}, ты {word}"
    elif field_name[1] == 'm':
        return f"{recipient}, вы {word}"
    else:
        raise RuntimeWarning(f"Ошибка определения числа и рода")


def get_praise_or_scold(bot, event, _type):
    if event.args:
        event.args[-1] = event.args[-1].replace('-', '')
    if event.original_args and event.args[-1] in gender_translator:
        translator_key = event.args[-1]
        del event.args[-1]
    else:
        try:
            user = bot.get_user_by_name(event.original_args, event.chat)
            if user.gender == '1':
                translator_key = 'ж1'
            else:
                translator_key = 'м1'
        except RuntimeWarning:
            translator_key = 'м1'
    if event.args:
        recipient = " ".join(event.args)

        if "петрович" in recipient.lower():
            if _type == 'bad':
                msg = random_event(BAD_ANSWERS)
            elif _type == 'good':
                msg = "спс))"
            else:
                msg = "wtf"
        else:
            word = get_from_db(gender_translator[translator_key], _type)
            msg = add_phrase_before(recipient, word, gender_translator[translator_key])
    else:
        msg = get_from_db(gender_translator[translator_key], _type)
    return msg


def get_praise_or_scold_self(event, _type):
    recipient = event.sender
    if recipient.gender == '1':
        translator_key = 'ж1'
    else:
        translator_key = 'м1'

    word = get_from_db(gender_translator[translator_key], _type)
    msg = add_phrase_before(recipient.name, word, gender_translator[translator_key])
    return msg


class Praise(CommonCommand):
    def __init__(self):
        names = ["похвалить", "похвали", "хвалить"]
        help_text = "Похвалить - рандомная похвала"
        detail_help_text = "Похвалить [кто-то] [род+число] - рандомная похвала\n" \
                           "Род и число указываются через последний аргумент: Мужской м, Женский ж, Средний с. Число: единственное *1, множественное *м\n" \
                           "Т.е. доступные сочетания аргументов могут быть следующими: [м ж с м1 ж1 с1 мм жм]\n" \
                           "Если в качестве параметра передаётся имя, фамилия, логин/id, никнейм, то род выберется из БД\n" \
                           "Пример. /похвалить бабушка ж"
        super().__init__(names, help_text, detail_help_text)

    def start(self):
        return get_praise_or_scold(self.bot, self.event, 'good')
