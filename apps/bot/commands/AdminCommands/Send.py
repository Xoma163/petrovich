from apps.bot.classes.Command import Command
from apps.bot.classes.bots.Bot import get_bot_by_platform
from apps.bot.classes.consts.Consts import Role


class Send(Command):
    name = "отправь"
    names = ["отправить", "сообщение"]
    help_text = "отправляет сообщение в любую конфу"
    help_texts = ["(id чата/название чата) (сообщение)"]
    access = Role.ADMIN

    def start(self):
        msg_chat_name = self.event.message.args[0]
        chat = self.bot.get_chat_by_name(msg_chat_name, False)
        msg = self.event.message.args_str.split(' ', 1)[1]
        bot = get_bot_by_platform(chat.get_platform_enum())()
        bot.send_message(chat.chat_id, msg)
        return "Отправил"
