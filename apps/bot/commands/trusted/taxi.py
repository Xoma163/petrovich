from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from petrovich.settings import STATIC_ROOT


class Taxi(Command):
    name = "такси"

    help_text = HelpText(
        commands_text="график отношения цены ко времени",
        help_texts=[
            HelpTextItem(Role.TRUSTED, [
                HelpTextItemCommand("[класс=эконом]", "график отношения цены ко времени")
            ])
        ],
        extra_text=(
            "Доступные классы - эконом, комфорт, комфорт+, экспресс, курьер"
        )
    )

    access = Role.TRUSTED

    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0] if self.event.message.args else None
        menu = [
            [["э", "эконом"], self.menu_econom],
            [["к", "комфорт"], self.menu_comfort],
            [["к+", "комфорт+"], self.menu_comfortplus],
            [["экспресс", "доставка"], self.menu_express],
            [["курьер"], self.menu_courier],
            [['default'], self.menu_econom]
        ]
        method = self.handle_menu(menu, arg0)
        rmi = method()
        return ResponseMessage(rmi)

    def menu_econom(self):
        return self.get_attachment_by_path(f"{STATIC_ROOT}/service/img/taxi/econom.png")

    def menu_comfort(self):
        return self.get_attachment_by_path(f"{STATIC_ROOT}/service/img/taxi/comfort.png")

    def menu_comfortplus(self):
        return self.get_attachment_by_path(f"{STATIC_ROOT}/service/img/taxi/comfortplus.png")

    def menu_express(self):
        return self.get_attachment_by_path(f"{STATIC_ROOT}/service/img/taxi/express.png")

    def menu_courier(self):
        return self.get_attachment_by_path(f"{STATIC_ROOT}/service/img/taxi/courier.png")

    def get_attachment_by_path(self, path) -> ResponseMessageItem:
        attachment = self.bot.get_photo_attachment(path, peer_id=self.event.peer_id, filename="petrovich_taxi.png")
        rmi = ResponseMessageItem(attachments=[attachment])
        return rmi
