from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.models import VkChat


class Conference(CommonCommand):
    def __init__(self):
        names = ["конфа", "конференция", "беседа"]
        help_text = "Конфа - назвать конфу"
        super().__init__(names, help_text, conversation=True, priority=90, api=False)

    def accept(self, event):
        if event.chat and (event.chat.name is None or event.chat.name == "") or event.command in self.names:
            return True

        return False

    def start(self):
        if self.event.command in self.names:
            if self.event.args:
                try:
                    self.check_sender(Role.CONFERENCE_ADMIN)
                    same_chats = VkChat.objects.filter(name=self.event.original_args)
                    if len(same_chats) > 0:
                        return "Конфа с таким названием уже есть. Придумайте другое"
                    self.event.chat.name = self.event.original_args
                    self.event.chat.save()
                    return f"Поменял название беседы на {self.event.original_args}"
                except RuntimeError as e:
                    if self.event.chat.admin is None:
                        msg = "Так как администратора конфы не было, то теперь вы стали администратором конфы!"
                        self.event.chat.admin = self.event.sender
                        same_chats = VkChat.objects.filter(name=self.event.original_args)
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
                    return "Конфа не имеет названия"
        else:
            return "Не задано имя конфы, задайте его командой /конфа (название конфы)"
