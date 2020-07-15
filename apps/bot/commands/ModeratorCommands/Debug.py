from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class Debug(CommonCommand):
    def __init__(self):
        names = ["дебаг"]
        help_text = "Дебаг - отображение распаршенного сообщения"
        super().__init__(names, help_text, access=Role.MODERATOR, platforms=['vk', 'tg'])

    def start(self):
        self.bot.DEBUG = not self.bot.DEBUG

        if self.bot.DEBUG:
            return 'Включил'
        else:
            return 'Выключил'
