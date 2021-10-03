from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand


class All(CommonCommand):
    name = "all"
    help_text = "присылает меншон по всем участникам конфы"
    help_texts = [
        "(текст) - присылает меншон по всем участникам конфы с текстом в начале"
    ]
    platforms = [Platform.TG]
    conversation = True

    def start(self):
        conversation_users = self.event.chat.users.all()
        if self.event.args:
            msg = f"{self.event.original_args}\n\n"
        else:
            msg = ""

        for user in conversation_users:
            msg += f"{self.bot.get_mention(user)}\n"
        return msg
