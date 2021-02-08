from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import find_command_by_name, get_help_for_command


class Help(CommonCommand):
    names = ["помощь", "хелп", "ман", "команды", "помоги", "памаги", "спаси", "хелб", "манул", "help", "start"]
    help_text = "Помощь - помощь по командам и боту"
    detail_help_text = "Очень смешно"

    def accept(self, event):
        # Самая первая кнопка клавы у бота
        if event.payload and event.payload['command'] == 'start':
            return True
        return super().accept(event)

    def start(self):
        if self.event.args:
            command = find_command_by_name(self.event.args[0].lower())
            self.check_sender(command.access)
            return get_help_for_command(command)
        text = "/помощь (название команды) - помощь по конкретной команде\n" \
               "/документация - документация по боту. Самый подробный мануал по всему в одном месте\n" \
               "/команды - список всех команд с кратким описанием\n" \
               "\n" \
               "Основы основ:\n" \
               "Пример конкретной команды: /рандом 10\n" \
               "* / — упоминание бота\n" \
               "* рандом — команда\n" \
               "* 10 — аргумент команды\n" \
               "\n" \
               "Формат детальной помощи по командам:\n" \
               "Команда - выполняет команду\n" \
               "Команда параметр - выполняет команду с параметром\n" \
               "Команда (аргумент) - выполняет команду с обязательным аргументом\n" \
               "Команда [аргумент=10] - выполняет команду с необязательным аргументом. Если не указать его, будет " \
               "подставлено значение по умолчанию"
        return text
