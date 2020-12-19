from wakeonlan import send_magic_packet

from apps.bot.classes.Consts import Role
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import WakeOnLanUserData


class WOL(CommonCommand):
    def __init__(self):
        names = ["пробуди", "разбуди", 'wol', 'wakeonlan']
        help_text = "Пробуди - пробуждает ваше устройство"
        detail_help_text = "Пробуди - пробуждает ваше устройство\n" \
                           "Пробуди (название) - пробуждает ваше устройство\n" \
                           "Для того, чтобы я добавил ваше устройство в базу - сообщите админу данные устройства"
        super().__init__(names, help_text, detail_help_text, access=Role.TRUSTED)

    def start(self):
        wol_data = WakeOnLanUserData.objects.filter(user=self.event.sender)

        if self.event.args:
            device_name = " ".join(self.event.args)
            wol_data = wol_data.filter(name__icontains=device_name)
        if not wol_data:
            raise PWarning("Не нашёл устройства для пробуждения. Напишите админу, чтобы добавить")
        if wol_data.count() > 1:
            wol_data_str = "\n".join([x.name for x in wol_data])
            msg = "Нашел несколько устройств. Уточните какое:\n" \
                  f"{wol_data_str}"
            raise PWarning(msg)
        else:
            wol_data = wol_data.first()
        send_magic_packet(wol_data.mac, ip_address=wol_data.ip, port=wol_data.port)
        return "Отправил"
