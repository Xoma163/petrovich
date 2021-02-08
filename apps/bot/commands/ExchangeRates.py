from apps.bot.APIs.CBRAPI import CBRAPI
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand


class ExchangeRates(CommonCommand):
    names = ["курс"]
    help_text = "Курс - курс валют"
    detail_help_text = "Курс - курс валют\n" \
                       "Курс [количество=1] (валюта) - перевод в другие валюты конкретное количество валюты"

    def start(self):
        filters_list = ["USD", "EUR", "NOK", "JPY", "GBP", "KZT", "UAH"]

        cbr_api = CBRAPI(filters_list)
        ex_rates = cbr_api.do()

        if self.event.args:
            self.check_args(1)
            if len(self.event.args) == 1:
                value = 1
                currency = self.event.args[0].lower()
            else:
                self.float_args = [0]
                self.parse_float()

                value = self.event.args[0]
                currency = self.event.args[1].lower()
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

        else:
            msg = "Курс валют:\n"
            for ex_rate in ex_rates:
                ex_rates[ex_rate]['value'] = self.to_fixed(ex_rates[ex_rate]['value'], 2)
                msg += f"{ex_rate} - {ex_rates[ex_rate]['value']} руб.\n"
            return msg

    @staticmethod
    def to_fixed(num, digits=0):
        return f"{num:.{digits}f}"
