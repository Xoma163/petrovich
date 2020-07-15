from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import Donations as DonationsModel


class Donations(CommonCommand):
    def __init__(self):
        names = ["донаты"]
        help_text = "Донаты - список всех донатов"
        super().__init__(names, help_text, access=Role.TRUSTED)

    def start(self):
        donations = DonationsModel.objects.all()
        if len(donations) == 0:
            return "Нема :("
        msg = ""
        total = {}
        for donation in donations:
            msg += f"{donation.username} - {donation.amount} {donation.currency}\n" \
                   f"{donation.message}\n\n"
            if donation.currency not in total:
                total[donation.currency] = float(donation.amount)
            else:
                total[donation.currency] += float(donation.amount)
        total_msg = ""
        for key in total:
            total_msg += f"{total[key]} {key}\n"
        msg += '------------------------------\n' \
               f'{total_msg}'
        return msg
