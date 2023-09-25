from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.service.models import Donations as DonationsModel


class Donations(Command):
    name = "донаты"
    name_tg = 'donations'
    help_text = "список всех донатов"
    access = Role.TRUSTED

    def start(self) -> ResponseMessage:
        donations = DonationsModel.objects.all()
        if len(donations) == 0:
            raise PWarning("Нема :(")
        msg = ""
        total = {}
        for donation in donations:
            msg += f"{donation.username} - {donation.amount} {donation.currency}\n"
            if donation.message:
                msg += f"{donation.message}\n"
            msg += "\n"

            if donation.currency not in total:
                total[donation.currency] = float(donation.amount)
            else:
                total[donation.currency] += float(donation.amount)
        total_msg = ""
        for key in total:
            total_msg += f"{total[key]} {key}\n"
        msg += f'{"-" * 30}\n' \
               f'{total_msg}'
        answer = msg
        return ResponseMessage(ResponseMessageItem(text=answer))
