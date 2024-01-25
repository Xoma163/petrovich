from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.palworld_server import PalworldServer

ps = PalworldServer()


class Palworld(Command):
    name = "palworld"
    names = ["пал", "палворлд", "палворд", "pal"]

    help_text = HelpText(
        commands_text="действия с сервером Palworld",
        help_texts=[
            HelpTextItem(Role.PALWORLD, [
                "- статус сервера",
                "старт - стартует сервер palworld",
                "стоп - стопит сервер palworld"
            ])
        ]
    )

    access = Role.PALWORLD

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None

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
        server = PalworldServer()
        server.start()

        answer = "Стартуем сервер"
        return ResponseMessageItem(text=answer)

    def menu_stop(self) -> ResponseMessageItem:
        self.check_args(1)
        server = PalworldServer()
        server.stop()

        answer = "Финишируем сервер"
        return ResponseMessageItem(text=answer)

    def menu_status(self) -> ResponseMessageItem:
        server = PalworldServer()
        server_info = server.get_server_info()
        answer = self.get_server_info_str(server, server_info)
        return ResponseMessageItem(text=answer)

    def get_server_info_str(self, server, server_info):
        if not server_info['online']:
            return "Palworld ⛔"

        player_range = f"({len(server_info['players'])}/{server_info['player_max']})"

        result = f"Palworld ✅ {player_range} - {server.HOST}:{server.PORT}"

        players = server_info['players']
        if players:
            players.sort(key=str.lower)
            players = [self.bot.get_formatted_text_line(player) for player in players]
            players_str = ", ".join(players)
            result += f"\nИгроки: {players_str}"
        return result
