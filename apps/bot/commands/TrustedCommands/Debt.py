from apps.bot.APIs.ZenmoneyAPI import ZenmoneyAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.utils.utils import decl_of_num


class Diary(Command):
    name = "долг"
    help_text = "ваш долг мне)0"
    access = Role.TRUSTED
    suggest_for_similar = False

    def start(self):
        z_api = ZenmoneyAPI()
        user_name = self.event.sender.name
        user_name = "Света"
        res = z_api.get_last_transactions_for_debt_by_name(user_name)

        if res['debt'] == 0:
            return "У тебя нет долгов. Вау!"
        elif res['debt'] < 0:
            roubles = decl_of_num(res['debt'], ["рубль", "рубля", "рублей"])
            return f"Я тебе должен {-res['debt']} {roubles}"
        else:
            transactions = []
            for transaction in res['transactions']:
                new_transaction = self.transform_transaction_to_str(transaction)
                transactions.append(new_transaction)

            transactions_str = "\n\n".join(transactions)

            roubles = decl_of_num(res['debt'], ["рубль", "рубля", "рублей"])
            return f"{transactions_str}\n----------\nИтого: {res['debt']} {roubles}"

