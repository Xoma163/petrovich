from apps.birds.CameraHandler import CameraHandler
from apps.bot.APIs.Minecraft import get_minecraft_version_by_args, MinecraftAPI
from apps.bot.classes.Consts import Role
from apps.bot.classes.DoTheLinuxComand import do_the_linux_command
from apps.bot.classes.common.CommonCommand import CommonCommand

cameraHandler = CameraHandler()


class Start(CommonCommand):
    def __init__(self):
        names = ["старт"]
        help_text = "Старт - возобновляет работу бота или модуля"
        detail_help_text = "Старт [сервис=бот [версия=1.15.1]] - стартует сервис\n" \
                           "Сервис - бот/синички/майнкрафт/террария\n" \
                           "Если майнкрафт, то может быть указана версия, 1.12.2 или 1.15.1"

        keyboard = [{'for': Role.ADMIN, 'text': 'Старт', 'color': 'green', 'row': 1, 'col': 1},
                    {'for': Role.ADMIN, 'text': 'Старт синички', 'color': 'green', 'row': 1, 'col': 3}]
        super().__init__(names, help_text, detail_help_text, keyboard=keyboard, access=Role.TRUSTED)

    def start(self):
        if self.event.args:
            arg0 = self.event.args[0].lower()
        else:
            arg0 = None

        menu = [
            [["синички"], self.menu_birds],
            [["майн", "майнкрафт", "mine", "minecraft"], self.menu_minecraft],
            [['террария', 'terraria'], self.menu_terraria],
            [['бот', 'bot'], self.menu_bot],
            [['default'], self.menu_bot]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_birds(self):
        self.check_sender(Role.ADMIN)
        if not cameraHandler.is_active():
            cameraHandler.resume()
            return "Стартуем синичек!"
        else:
            return "Синички уже стартовали"

    def menu_minecraft(self):
        self.check_sender(Role.MINECRAFT)
        version = None
        if len(self.event.args) > 1:
            version = self.event.args[1]
        minecraft_server = get_minecraft_version_by_args(version)
        if not minecraft_server:
            return "Я не знаю такой версии"
        version = minecraft_server['names'][0]
        self.check_command_time(f'minecraft_{version}', minecraft_server['delay'])
        minecraft_api = MinecraftAPI(
            version,
            bot=self.bot,
            event=self.event,
            amazon=minecraft_server['amazon'])
        minecraft_api.start()

        message = f"Стартуем майн {version}"
        return message

    def menu_terraria(self):
        self.check_sender(Role.TERRARIA)
        self.check_command_time('terraria', 10)
        do_the_linux_command('sudo systemctl start terraria')
        return "Стартуем террарию!"

    def menu_bot(self):
        self.check_sender(Role.ADMIN)
        self.bot.BOT_CAN_WORK = True
        cameraHandler.resume()
        return "Стартуем!"
