from apps.bot.classes.Consts import Role, Platform
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand


class Conference(CommonCommand):
    names = ["конфа", "конференция", "беседа"]
    help_text = "Конфа - назвать конфу"
    conversation = True
    priority = 90
    platforms = [Platform.VK, Platform.TG]

    def accept(self, event):
        if event.chat and (event.chat.name is None or event.chat.name == ""):
            return True
        return super().accept(event)

    def start(self):
        if self.event.command not in self.names:
            raise PWarning("Не задано имя конфы, задайте его командой /конфа (название конфы)")
        if self.event.args:
            try:
                self.check_sender(Role.CONFERENCE_ADMIN)
                same_chats = self.bot.chat_model.filter(name=self.event.original_args)
                if len(same_chats) > 0:
                    raise PWarning("Конфа с таким названием уже есть. Придумайте другое")
                self.event.chat.name = self.event.original_args
                self.event.chat.save()
                return f"Поменял название беседы на {self.event.original_args}"
            except PWarning as e:
                if self.event.chat.admin is None:
                    msg = "Так как администратора конфы не было, то теперь вы стали администратором конфы!"
                    self.event.chat.admin = self.event.sender
                    same_chats = self.bot.chat_model.filter(name=self.event.original_args)
                    if len(same_chats) > 0:
                        msg += "\nКонфа с таким названием уже есть. Придумайте другое"
                        return msg
                    self.event.chat.name = self.event.original_args
                    self.event.chat.save()
                    msg += f"\nПоменял название беседы на {self.event.original_args}"
                    return msg
                else:
                    return str(e)

        else:
            if self.event.chat.name and self.event.chat.name != "":
                return f"Название конфы - {self.event.chat.name}"
            else:
                raise PWarning("Конфа не имеет названия")
