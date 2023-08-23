from apps.bot.classes.Command import Command
from apps.bot.classes.messages.ResponseMessage import ResponseMessage
from apps.bot.commands.Praise import get_praise_or_scold


class Scold(Command):
    name = "обосрать"
    names = ["обосри", "поругать", "поругай"]
    name_tg = 'scold'
    help_text = "рандомное оскорбление"
    help_texts = [
        "Обосрать [кто-то] [род+число] - рандомное оскорбление"
    ]
    help_texts_extra = \
        "Род и число указываются через последний аргумент: Мужской м, Женский ж, Средний с. Число: единственное *1, множественное *м\n" \
        "Т.е. доступные сочетания аргументов могут быть следующими: [м ж с м1 ж1 с1 мм жм]\n" \
        "Если в качестве параметра передаётся имя, фамилия, логин/id, никнейм, то род выберется из БД\n" \
        "Пример. /обосрать бабушка ж"

    def start(self) -> ResponseMessage:
        rmi = get_praise_or_scold(self.bot, self.event, 'bad')
        return ResponseMessage(rmi)
