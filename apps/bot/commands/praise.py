from apps.bot.classes.command import Command
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
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
        raise PWarning("Нет такого слова :(")
    except Exception as e:
        raise PWarning("Нет такого слова :(\n"
                       f"Ошибка - {str(e)}")
    return word


def add_phrase_before(recipient, word, field_name):
    if field_name[1] == '1':
        return f"{recipient}, ты {word}"
    elif field_name[1] == 'm':
        return f"{recipient}, вы {word}"
    else:
        raise PWarning("Ошибка определения числа и рода")


def get_praise_or_scold(bot, event, _type) -> ResponseMessageItem:
    if event.message.args_str and event.message.args[-1].replace('-', '') in gender_translator:
        translator_key = event.message.args[-1].replace('-', '')
        args_case = event.message.args_case[:-1]
    else:
        try:
            user = bot.get_profile_by_name(event.message.args_str, event.chat)
            if user.gender == '1':
                translator_key = 'ж1'
            else:
                translator_key = 'м1'
        except PWarning:
            translator_key = 'м1'
        args_case = event.message.args_case

    if event.message.args:
        recipient = " ".join(args_case)

        if "петрович" in recipient.lower() and _type == 'good':
            answer = "спс))"
        else:
            answer = get_from_db(gender_translator[translator_key], _type)
            if recipient:
                answer = add_phrase_before(recipient, answer, gender_translator[translator_key])

    else:
        answer = get_from_db(gender_translator[translator_key], _type)
    return ResponseMessageItem(text=answer)


def get_praise_or_scold_self(event, _type) -> str:
    recipient = event.sender
    if recipient.gender == '1':
        translator_key = 'ж1'
    else:
        translator_key = 'м1'

    word = get_from_db(gender_translator[translator_key], _type)
    msg = add_phrase_before(recipient.name, word, gender_translator[translator_key])
    return msg


class Praise(Command):
    name = 'похвалить'
    names = ["похвали", "хвалить"]
    name_tg = 'praise'
    help_text = "рандомная похвала"
    help_texts = ["Похвалить [кто-то] [род+число] - рандомная похвала"]
    help_texts_extra = \
        "Род и число указываются через последний аргумент: Мужской м, Женский ж, Средний с. Число: единственное *1, множественное *м\n" \
        "Т.е. доступные сочетания аргументов могут быть следующими: [м ж с м1 ж1 с1 мм жм]\n" \
        "Если в качестве параметра передаётся имя, фамилия, логин/id, никнейм, то род выберется из БД\n" \
        "Пример. /похвалить бабушка ж"

    def start(self) -> ResponseMessage:
        rmi = get_praise_or_scold(self.bot, self.event, 'good')
        return ResponseMessage(rmi)
