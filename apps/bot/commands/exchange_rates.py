from apps.bot.api.cbr import CBRAPI
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class ExchangeRates(Command):
    name = "курс"

    help_text = HelpText(
        commands_text="курс валют",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextArgument(None, "курс валют"),
                HelpTextArgument("[количество=1] (валюта)", "перевод в другие валюты конкретное количество валюты")
            ])
        ]
    )

    def start(self) -> ResponseMessage:
        filters_list = ["USD", "EUR", "NOK", "JPY", "GBP", "KZT", "UAH", "AMD", "UZS"]

        cbr_api = CBRAPI(filters_list, log_filter=self.event.log_filter)
        ex_rates = cbr_api.get_ex_rates()

        if self.event.message.args:
            answer = self.concrete_rate(ex_rates)
        else:
            answer = self.all_rates(ex_rates)
        return ResponseMessage(ResponseMessageItem(text=answer))

    def concrete_rate(self, ex_rates: dict) -> str:
        self.check_args(1)
        if len(self.event.message.args) == 1:
            value = 1
            currency = self.event.message.args[0]
        else:
            self.float_args = [0]
            self.parse_float()

            value = self.event.message.args[0]
            currency = self.event.message.args[1]
        if any(ext in currency for ext in ['rub', "руб"]):
            msg = "Перевод в другие валюты:\n"
            for ex_rate in ex_rates:
                total_value = self.to_fixed(value / ex_rates[ex_rate]['value'], 2)
                msg += f"{total_value} {ex_rate}\n"
            return msg
        else:
            for code in ex_rates:
                if currency[:5] in ex_rates[code]['name'] or currency in code.lower():
                    total_value = self.to_fixed(value * ex_rates[code]['value'], 2)
                    msg = "Перевод в рубли:\n"
                    msg += f"{total_value} руб."
                    return msg
            raise PWarning("Пока не знаю как переводить из этой валюты")

    def all_rates(self, ex_rates: dict) -> str:
        msg = "Курс валют:\n"
        for ex_rate in ex_rates:
            ex_rates[ex_rate]['value'] = self.to_fixed(ex_rates[ex_rate]['value'], 4)
            msg += f"{ex_rate} - {ex_rates[ex_rate]['value']} руб.\n"
        return msg

    @staticmethod
    def to_fixed(num: float, digits=0) -> str:
        return f"{num:.{digits}f}"
