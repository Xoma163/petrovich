from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning


class All(Command):
    name = "all"
    name_tg = "all"

    help_text = "присылает меншон по всем участникам конфы"
    help_texts = [
        " - присылает меншон по всем участникам конфы",
        "(текст) - присылает меншон по всем участникам конфы с текстом в начале"
    ]
    platforms = [Platform.TG]
    conversation = True

    def start(self):
        conversation_users = self.event.chat.users.all().exclude(pk=self.event.sender.pk)
        if len(conversation_users) == 0:
            raise PWarning("В конфе нет людей((")
        if self.event.message.args:
            msg = f"{self.event.message.args_str_case}\n\n"
        else:
            msg = ""

        for user in conversation_users:
            msg += f"{self.bot.get_mention(user)}\n"
        return msg
