from apps.bot.api.minecraft_server import MinecraftServer
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from petrovich.settings import MAIN_DOMAIN


class Minecraft(Command):
    name = "майнкрафт"
    names = ["майн", "mine", "minecraft"]

    help_text = HelpText(
        commands_text="действия с сервером майнкрафта",
        help_texts=[
            HelpTextItem(Role.MINECRAFT, [
                HelpTextArgument(None, "статус по всем серверам"),
                HelpTextArgument("старт", "стартует сервер"),
                HelpTextArgument("стоп", "останавливает сервер")
            ])
        ]
    )

    access = Role.MINECRAFT

    server = MinecraftServer(
        ip=MAIN_DOMAIN,
        port=25565,
        delay=60,
        names=['1.20.1', "1.20"],
        service_name="minecraft",
        map_url=f"https://minecraft-map.{MAIN_DOMAIN}/",
    )

    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0] if self.event.message.args else None

        menu = [
            [["старт", "start"], self.menu_start],
            [["стоп", "stop"], self.menu_stop],
            [["статус", "status"], self.menu_status],
            [['default'], self.menu_status]
        ]
        method = self.handle_menu(menu, arg0)
        rmi = method()
        return ResponseMessage(rmi)

    def menu_start(self) -> ResponseMessageItem:
        self.check_args(1)
        self.server.start()

        answer = "Стартуем майн"
        return ResponseMessageItem(text=answer)

    def menu_stop(self) -> ResponseMessageItem:
        self.check_args(1)
        self.server.stop()
        answer = "Финишируем майн"
        return ResponseMessageItem(text=answer)

    def menu_status(self) -> ResponseMessageItem:
        self.server.get_server_info()
        answer = self.get_server_info_str(self.server)

        button = self.bot.get_button("Обновить", self.name, args=['статус'])
        keyboard = self.bot.get_inline_keyboard([button])
        mid = self.event.raw.get('callback_query', {}).get('message', {}).get('message_id')
        return ResponseMessageItem(text=answer, keyboard=keyboard, message_id=mid)

    def get_server_info_str(self, server):
        if not server.server_info.online:
            return f"Майн {server.get_version()} ⛔"

        version = server.server_info.version
        player_range = f"({server.server_info.players_online}/{server.server_info.players_max})"

        server_address = server.ip if server.port == server.DEFAULT_PORT else f'{server.ip}:{server.port}'
        result = f"Майн {version} ✅ {player_range} - {self.bot.get_formatted_text_line(server_address)}"

        players = server.server_info.players
        if players:
            players.sort(key=lambda x: x.name)
            players = [self.bot.get_formatted_text_line(player) for player in players]
            players_str = ", ".join(players)
            result += f"\nИгроки: {players_str}"
        if server.map_url:
            map_url = self.bot.get_formatted_url("Карта", server.map_url)
            result += f"\n{map_url}"
        return result
