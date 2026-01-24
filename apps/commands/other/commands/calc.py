import math

from apps.bot.consts import RoleEnum
from apps.bot.core.event.event import Event
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.shared.exceptions import PWarning
from apps.shared.utils.calculator import Calculator


class Calc(Command):
    name = "="
    names = ["калькулятор", "кальк"]

    help_text = HelpText(
        commands_text="калькулятор",
        help_texts=[
            HelpTextItem(RoleEnum.USER, [
                HelpTextArgument("(выражение)", "калькулятор выражений. Умеет работать с + - * / ^ ( )")
            ])
        ]
    )

    MAX_OPERATIONS = 20

    def accept(self, event: Event) -> bool:
        if event.message and event.message.clear and event.message.clear[0] == '=':
            return True
        return super().accept(event)

    def start(self) -> ResponseMessage:
        expression = self.get_expression()
        operations_count = sum(
            expression.count(x.character) for x in Calculator.COMPUTABLE_SYMBOLS if hasattr(x, 'character')
        )
        if operations_count > self.MAX_OPERATIONS:
            raise PWarning("Слишком много операций, процессор перегреется((")

        result = self.calculate(expression)
        return ResponseMessage(ResponseMessageItem(text=result))

    def get_expression(self):
        if self.event.message.clear[0] == '=':
            expression = self.event.message.clear[1:]
        else:
            self.check_args(1)
            expression = self.event.message.args_str
        expression = expression \
            .replace(' ', '') \
            .replace(',', '.')
        expression = self.replace_consts(expression) \
            .replace('k', '000') \
            .replace('к', '000') \
            .replace('m', "000000") \
            .replace('м', "000000")
        return expression

    @staticmethod
    def calculate(expression) -> str:
        calculator = Calculator()
        return calculator.calculate(expression)

    @staticmethod
    def replace_consts(expression):
        pi = str(math.pi)
        expression = expression.replace('pi', pi).replace('пи', pi)
        e = str(math.e)
        expression = expression.replace('e', e).replace('е', e)
        return expression
