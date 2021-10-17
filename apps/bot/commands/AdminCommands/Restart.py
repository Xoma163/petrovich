from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command


class Restart(Command):
    name = "рестарт"
    names = ["ребут"]
    help_text = "перезагружает бота или веб на сервере, либо сам сервер"
    help_texts = ["[сервис=бот] - перезагружает сервис\nСервис - бот/веб/сервер"]
    access = Role.ADMIN

    def start(self):
        if self.event.message.args:
            arg0 = self.event.message.args[0].lower()
        else:
            arg0 = None
        menu = [
            [['бот'], self.menu_bot],
            [['веб', 'сайт'], self.menu_web],
            [['сервер'], self.menu_server],
            [['default'], self.menu_bot]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_bot(self):
        self.bot.parse_and_send_msgs_thread(self.event.peer_id, 'Рестартим бота')
        do_the_linux_command('sudo systemctl restart petrovich')
        return 'Рестартим бота'

    def menu_web(self):
        self.bot.parse_and_send_msgs_thread(self.event.peer_id, 'Рестартим веб')
        do_the_linux_command('sudo systemctl restart petrovich_site')
        return 'Рестартим веб'

    def menu_server(self):
        self.bot.parse_and_send_msgs_thread(self.event.peer_id, 'Рестартим сервер')
        do_the_linux_command('sudo systemctl reboot -i')
        return 'Рестартим сервер'
