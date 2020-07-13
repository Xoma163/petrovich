from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class Control(CommonCommand):
    def __init__(self):
        names = ["отправить", "сообщение"]
        help_text = "Отправить - отправление сообщение в любую конфу"
        detail_help_text = "Отправить (id чата/название чата) (сообщение)"
        super().__init__(names, help_text, detail_help_text, access=Role.ADMIN, args=2)

    def start(self):
        try:
            self.int_args = [0]
            self.parse_int()
            msg_chat_id = self.event.args[0]
            chat = self.bot.get_group_id(msg_chat_id)
        except RuntimeError:
            msg_chat_name = self.event.args[0]
            chat = self.bot.get_chat_by_name(msg_chat_name)
        msg = self.event.original_args.split(' ', 1)[1]
        if self.event.platform == 'vk':
            self.bot.send_message(chat.chat_id, msg)
        elif self.event.platform == 'tg':
            self.bot.send_message(f'-{chat.chat_id}', msg)
