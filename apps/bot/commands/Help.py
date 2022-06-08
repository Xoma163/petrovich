from apps.bot.classes.Command import Command
from apps.bot.utils.utils import find_command_by_name, get_help_texts_for_command


class Help(Command):
    name = "помощь"
    names = ["хелп", "ман", "помоги", "памаги", "спаси", "хелб", "манул", "help", "start"]
    help_text = "помощь по командам и боту"

    def accept(self, event):
        # Самая первая кнопка клавы у бота
        if event.payload and event.payload['c'] == 'start':
            return True
        return super().accept(event)

    def start(self):
        if self.event.message.args:
            command = find_command_by_name(self.event.message.args[0])
            self.check_sender(command.access)
            help_text = get_help_texts_for_command(command, self.event.platform)
            return help_text
        text = \
            "/помощь (название команды) - помощь по конкретной команде\n" \
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
            "Команда [аргумент=10] - выполняет команду с необязательным аргументом. Если не указать его, будет подставлено значение по умолчанию"
        return text
