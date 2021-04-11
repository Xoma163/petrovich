from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.commands.Praise import get_praise_or_scold


class Scold(CommonCommand):
    name = "обосрать"
    names = ["обосри", "поругать", "поругай"]
    help_text = "рандомное оскорбление"
    help_texts = [
        "Обосрать [кто-то] [род+число] - рандомное оскорбление\n"
        "Род и число указываются через последний аргумент: Мужской м, Женский ж, Средний с. Число: единственное *1, множественное *м\n"
        "Т.е. доступные сочетания аргументов могут быть следующими: [м ж с м1 ж1 с1 мм жм]\n"
        "Если в качестве параметра передаётся имя, фамилия, логин/id, никнейм, то род выберется из БД\n"
        "Пример. /обосрать бабушка ж"
    ]
    platforms = [Platform.VK, Platform.TG, Platform.API]

    def start(self):
        return get_praise_or_scold(self.bot, self.event, 'bad')
