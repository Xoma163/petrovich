from apps.bot.classes.Consts import Role
from apps.bot.classes.bots.CommonBot import get_bot_by_platform
from apps.bot.classes.common.CommonCommand import CommonCommand


class Control(CommonCommand):
    names = ["отправить", "сообщение", "отправь"]
    help_text = "Отправить - отправление сообщение в любую конфу"
    detail_help_text = "Отправить (id чата/название чата) (сообщение)"
    access = Role.ADMIN

    def start(self):
        msg_chat_name = self.event.args[0]
        chat = self.bot.get_chat_by_name(msg_chat_name, False)
        msg = self.event.original_args.split(' ', 1)[1]
        bot = get_bot_by_platform(chat.get_platform_enum())()
        bot.send_message(chat.chat_id, msg)
        return "Отправил"
