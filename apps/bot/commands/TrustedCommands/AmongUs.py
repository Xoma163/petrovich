from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class AmongUs(CommonCommand):
    def __init__(self):
        names = ["amongus", "амонгас", "among", 'амонг']
        help_text = "Amongus - зовёт всех играть"
        super().__init__(names, help_text, access=Role.TRUSTED)

    def start(self):
        user_notifications = "@xoma163\n" \
                             "@lana.chern\n" \
                             "@ma_maksim\n" \
                             "@eatm0re\n" \
                             "@mstop\n" \
                             "@e.korsakov\n"
        return user_notifications
