from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage
from apps.bot.commands.praise import get_praise_or_scold


class Scold(Command):
    name = "обосрать"
    names = ["обосри", "поругать", "поругай"]

    help_text = HelpText(
        commands_text="рандомное оскорбление",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("Обосрать [кто-то] [род+число]", "рандомное оскорбление")
            ])
        ],

        extra_text=(
            "Род и число указываются через последний аргумент: Мужской м, Женский ж, Средний с. Число: единственное *1, множественное *м\n"
            "Т.е. доступные сочетания аргументов могут быть следующими: [м ж с м1 ж1 с1 мм жм]\n"
            "Если в качестве параметра передаётся имя, фамилия, логин/id, никнейм, то род выберется из БД\n"
            "Пример. /обосрать бабушка ж"
        ),
    )

    def start(self) -> ResponseMessage:
        rmi = get_praise_or_scold(self.bot, self.event, 'bad')
        return ResponseMessage(rmi)
