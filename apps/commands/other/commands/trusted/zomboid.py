from apps.bot.consts import RoleEnum
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextArgument, HelpTextItem, HelpTextKey
from apps.connectors.parsers.zomboid.zomboid_server import ZomboidServer, ZomboidServerData
from apps.shared.utils.utils import check_command_time
from petrovich.settings import ZOMBOID_RCON_HOST, ZOMBOID_RCON_PASSWORD, ZOMBOID_RCON_PORT


class Zomboid(Command):
    RESTART_DELAY = 180

    name = "зомбоид"
    names = ["zomboid"]
    access = RoleEnum.TRUSTED

    help_text = HelpText(
        commands_text="статус и рестарт сервера Project Zomboid",
        help_texts=[
            HelpTextItem(
                access,
                [
                    HelpTextArgument(None, "статус сервера"),
                    HelpTextArgument("рестарт", "перезапускает сервер"),
                ],
            ),
            HelpTextItem(
                RoleEnum.ADMIN,
                [
                    HelpTextArgument("рестарт", "перезапускает сервер"),
                ],
            ),
        ],
        help_text_keys=[
            HelpTextItem(
                RoleEnum.ADMIN,
                [
                    HelpTextKey("force", None, "форсированно перезапускает сервер"),
                ],
            ),
        ],
    )

    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0] if self.event.message.args else None

        menu = [
            [["рестарт", "restart"], self.menu_restart],
            [["статус", "status"], self.menu_status],
            [["default"], self.menu_status],
        ]
        method = self.handle_menu(menu, arg0)
        rmi = method()
        return ResponseMessage(rmi)

    def menu_restart(self) -> ResponseMessageItem:
        self.check_args(1)
        force = self.event.message.is_key_provided({"force"})
        server = self.get_server()
        if force:
            self.check_sender(RoleEnum.ADMIN)
            server.force_restart()
            return ResponseMessageItem(text="Форсированно рестартим Zomboid")

        check_command_time("zomboid", self.RESTART_DELAY)
        server.restart()
        return ResponseMessageItem(text="Рестартим Zomboid")

    def menu_status(self) -> ResponseMessageItem:
        server = self.get_server()
        server_info = server.get_server_info()
        answer = self.get_server_info_str(server_info)

        button = self.bot.get_button("Обновить", self.name, args=["статус"])
        keyboard = self.bot.get_inline_keyboard([button])
        mid = self.event.raw.get("callback_query", {}).get("message", {}).get("message_id")
        return ResponseMessageItem(text=answer, keyboard=keyboard, message_id=mid)

    def get_server_info_str(self, server_info: ZomboidServerData) -> str:
        if server_info.players_online is None:
            return "Zomboid: не нашёл список игроков в ответе сервера"

        answer = f"Zomboid ✅ Игроков: {server_info.players_online}"
        if server_info.players:
            players = sorted(server_info.players)
            players = [self.bot.get_formatted_text_line(player) for player in players]
            answer += f"\nИгроки: {', '.join(players)}"
        return answer

    def get_server(self) -> ZomboidServer:
        return ZomboidServer(
            rcon_host=ZOMBOID_RCON_HOST,
            rcon_port=ZOMBOID_RCON_PORT,
            rcon_password=ZOMBOID_RCON_PASSWORD,
            log_filter=self.event.log_filter,
        )
