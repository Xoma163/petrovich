from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import get_help_texts_for_command


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
            command = self.find_command_by_name(self.event.message.args[0])
            self.check_sender(command.access)
            help_text = get_help_texts_for_command(command, self.event.platform)
            return help_text
        text = \
            f"{self.bot.get_formatted_text_line('/помощь')} (название команды) - помощь по конкретной команде\n" \
            f"{self.bot.get_formatted_text_line('/документация')} - документация по боту. Самый подробный мануал по всему в одном месте\n" \
            f"{self.bot.get_formatted_text_line('/команды')} - список всех команд с кратким описанием\n" \
            "\n" \
            "Основы основ:\n" \
            f"Пример конкретной команды: {self.bot.get_formatted_text_line('/рандом 10')}\n" \
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

    @staticmethod
    def find_command_by_name(command_name: str):
        """
        Ищет команду по имени
        """
        from apps.bot.initial import COMMANDS
        for command in COMMANDS:
            if command_name == command.name or (command.names and command_name in command.names):
                return command
        raise PWarning("Я не знаю такой команды")
