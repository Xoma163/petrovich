import io

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.utils.DoTheLinuxComand import do_the_linux_command
from apps.bot.utils.utils import draw_text_on_image
from petrovich.settings import BASE_DIR


class Logs(Command):
    name = "логи"
    names = ["лог"]
    name_tg = 'logs'

    help_text = "логи бота"
    help_texts = [
        "[сервис=бот/сервер] [кол-во строк=50] - логи. Макс 1000 строк."
    ]

    access = Role.MODERATOR
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        arg0 = None
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        menu = [
            [['веб', 'web', 'сайт', 'site'], self.get_web_logs],
            [['бот', 'bot'], self.get_bot_logs],
            [['default'], self.get_bot_logs]
        ]
        method = self.handle_menu(menu, arg0)
        image = method()

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return {'attachments': self.bot.upload_document(img_byte_arr, peer_id=self.event.peer_id, filename='logs.png')}

    def get_web_logs(self):
        count = self.get_count(50, 1000)
        command = f"systemctl status petrovich_site -n{count}"
        res = self.get_server_logs(command)
        img = draw_text_on_image(res)
        return img

    def get_bot_logs(self):
        count = self.get_count(50, 1000)
        command = f"systemctl status petrovich -n{count}"
        res = self._get_bot_logs(command)
        img = draw_text_on_image(res)
        return img

    def get_server_logs(self, command):
        output = do_the_linux_command(command)

        # Обрезаем инфу самого systemctl
        index_command = output.find(command)
        if index_command != -1:
            output = output[index_command + len(command) + 1:]
        else:
            start_command = f"{BASE_DIR}/venv/bin/uwsgi --ini {BASE_DIR}/config/uwsgi.ini"
            index_command = output.rfind(start_command)
            if index_command != -1:
                output = output[index_command + len(start_command) + 1:]

        # Удаляем всё до старта
        start_string = "*** uWSGI is running in multiple interpreter mode ***"
        if output.find(start_string) != -1:
            output = output[output.find(start_string) + len(start_string):]

        # Удаляем везде вхождения этой ненужной строки
        index_removing = output.find("server python[")
        if index_removing != -1:
            for_removing = output[index_removing:output.find(']', index_removing + 1) + 1]
            output = output.replace(for_removing, '')

        output = "Логи:\n" + output + "\n"
        words = ["GET", "POST", "spawned uWSGI", "Not Found:", "HEAD", "pidfile", "WSGI app 0", "Bad Request",
                 "HTTP_HOST", "OPTIONS "]
        for word in words:
            output = self.remove_rows_if_find_word(output, word)
        return output

    def _get_bot_logs(self, command):
        output = do_the_linux_command(command)

        # Обрезаем инфу самого systemctl
        index_command = output.find(command)
        if index_command != -1:
            output = output[index_command + len(command) + 1:]

        index_removing = output.find("server python[")
        if index_removing != -1:
            for_removing = output[index_removing:output.find(']', index_removing + 1) + 1]
            output = output.replace(for_removing, '')
        words = ["USER=root", "user root", "Stopped", "Started"]
        for word in words:
            output = self.remove_rows_if_find_word(output, word)
        output = "Логи:\n" + output + "\n"
        return output

    def get_count(self, default, max_count):
        if self.event.message.args:
            try:
                count = int(self.event.message.args[-1])
                return min(count, max_count)
            except ValueError:
                pass
        return default

    @staticmethod
    def remove_rows_if_find_word(old_str, word):
        while old_str.find(word) != -1:
            word_index = old_str.find(word)
            left_index = old_str.rfind('\n', 0, word_index - len(word))
            right_index = old_str.find('\n', word_index)
            old_str = old_str[:left_index] + old_str[right_index:]
        return old_str
