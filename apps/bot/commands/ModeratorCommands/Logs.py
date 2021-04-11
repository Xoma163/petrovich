import io

import pytz

from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.DoTheLinuxComand import do_the_linux_command
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import draw_text_on_image
from apps.db_logger.models import Logger
from petrovich.settings import BASE_DIR, DEFAULT_TIME_ZONE


def remove_rows_if_find_word(old_str, word):
    while old_str.find(word) != -1:
        word_index = old_str.find(word)
        left_index = old_str.rfind('\n', 0, word_index - len(word))
        right_index = old_str.find('\n', word_index)
        old_str = old_str[:left_index] + old_str[right_index:]
    return old_str


def get_server_logs(command):
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
        output = remove_rows_if_find_word(output, word)
    return output


def get_bot_logs(command):
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
        output = remove_rows_if_find_word(output, word)
    output = "Логи:\n" + output + "\n"
    return output


class Logs(CommonCommand):
    name = "логи"
    names = ["лог"]
    help_text = "логи бота или сервера"
    help_texts = [
        "[сервис=бот] [кол-во строк=50] - логи. Сервис - бот/сервер. Макс 1000 строк.",
        "бд [кол-во записей = 1] - последний лог с трейсбеком. Макс 5 записей",
    ]
    keyboard = {'for': Role.MODERATOR, 'text': 'Логи', 'color': 'blue', 'row': 1, 'col': 1}
    access = Role.MODERATOR
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        arg0 = None
        if self.event.args:
            arg0 = self.event.args[0].lower()
        menu = [
            [['веб', 'web', 'сайт', 'site'], self.get_web_logs],
            [['бот', 'bot'], self.get_bot_logs],
            [['бд'], self.get_db_logs],
            [['default'], self.get_bot_logs]
        ]
        method = self.handle_menu(menu, arg0)
        image = method()

        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        # if image.height > 1500:
        return {'attachments': self.bot.upload_document(img_byte_arr, peer_id=self.event.peer_id)}
        # else:
        #     return {'attachments': self.bot.upload_photos(img_byte_arr)}

    def get_web_logs(self):
        count = self.get_count(50, 1000)
        command = f"systemctl status petrovich_site -n{count}"
        res = get_server_logs(command)
        img = draw_text_on_image(res)
        return img

    def get_bot_logs(self):
        count = self.get_count(50, 1000)
        command = f"systemctl status petrovich -n{count}"
        res = get_bot_logs(command)
        img = draw_text_on_image(res)
        return img

    def get_db_logs(self):
        count = self.get_count(1, 5)
        logs = Logger.objects.filter(traceback__isnull=False)[:count]
        if not logs:
            raise PWarning("Не нашёл логов с ошибками")
        msg = ""
        for log in logs:
            if self.event.sender.city:
                tz = self.event.sender.city.timezone.name
            else:
                tz = DEFAULT_TIME_ZONE

            msg += f"{log.create_datetime.astimezone(pytz.timezone(tz)).strftime('%d.%m.%Y %H:%M:%S')}\n\n" \
                   f"{log.exception}\n\n" \
                   f"{log.traceback}\n\n" \
                   f"---------------------------------------------------------------------------------------------------------\n\n"
        img = draw_text_on_image(msg)
        return img

    def get_count(self, default, max_count):
        if self.event.args:
            try:
                count = int(self.event.args[-1])
                return min(count, max_count)
            except ValueError:
                pass
        return default
