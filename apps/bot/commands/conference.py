from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Conference(Command):
    name = "конфа"
    names = ["конференция", "беседа"]
    help_text = "назвать конфу"
    help_texts = ["(название конфы) - называет конфу"]
    conversation = True
    mentioned = True
    priority = 90
    platforms = [Platform.TG]

    bot: TgBot

    def accept(self, event: Event) -> bool:
        if event.chat and (event.chat.name is None or event.chat.name == ""):
            return True
        return super().accept(event)

    def start(self) -> ResponseMessage:
        if self.event.message.command not in self.full_names:
            raise PWarning(
                "Не задано имя конфы\n"
                f"Задайте его командой {self.bot.get_formatted_text_line('/' + self.name)} (название конфы)"
            )
        if self.event.message.args:
            self.event.chat.name = self.event.message.args_str_case
            self.event.chat.save()
            answer = f"Поменял название беседы на {self.event.chat.name}"
            return ResponseMessage(ResponseMessageItem(text=answer))
        elif self.event.chat.name and self.event.chat.name != "":
            answer = f"Название конфы - {self.event.chat.name}"
            return ResponseMessage(ResponseMessageItem(text=answer))
        else:
            raise PWarning(
                f"Конфа не имеет названия\n"
                f"задайте его командой {self.bot.get_formatted_text_line('/' + self.name)} (название конфы)"
            )
