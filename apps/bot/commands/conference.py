from threading import Lock

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem

lock = Lock()


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
        with lock:
            if self.event.message.command not in self.full_names:
                raise PWarning("Не задано имя конфы, задайте его командой /конфа (название конфы)")
            if self.event.message.args:
                try:
                    self.check_sender(Role.CONFERENCE_ADMIN)
                    self.event.chat.name = self.event.message.args_str_case
                    self.event.chat.save()
                    answer = f"Поменял название беседы на {self.event.message.args_str_case}"
                    return ResponseMessage(ResponseMessageItem(text=answer))
                except PWarning as e:
                    if self.event.chat.admin:
                        answer = str(e)
                        return ResponseMessage(ResponseMessageItem(text=answer))
                    answer = "Так как администратора конфы не было, то теперь вы стали администратором конфы!"
                    self.event.chat.admin = self.event.sender
                    self.event.chat.name = self.event.message.args_str_case
                    self.event.chat.save()
                    answer += f"\nПоменял название беседы на {self.event.message.args_str_case}"
                    return ResponseMessage(ResponseMessageItem(text=answer))
            elif self.event.chat.name and self.event.chat.name != "":
                answer = f"Название конфы - {self.event.chat.name}"
                return ResponseMessage(ResponseMessageItem(text=answer))
            else:
                raise PWarning("Конфа не имеет названия")
