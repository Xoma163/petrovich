import re


class Message:
    COMMAND_SYMBOLS = ['/', '!']

    def __init__(self, raw_str=None, _id=None):
        """
        raw - исходная строка
        clear - произведены замены ',' на пробел, переведено в нижний регистр, ё->е

        command - команда
        args_str - аргументы строкой
        args - аргументы списком
        """
        self.has_command_symbols = False

        if not raw_str:
            return
        self.raw = raw_str

        if self.raw[0] in self.COMMAND_SYMBOLS:
            self.has_command_symbols = True
            self.raw = self.raw[1:]
        self.clear = self.get_cleared_message(self.raw)
        msg_split = self.clear.split(' ', 1)

        self.command = msg_split[0].lower()
        self.args_str = None
        self.args = None
        if len(msg_split) > 1:
            self.args_str = msg_split[1]
            self.args = self.args_str.split(' ')

        self.id = _id

    @staticmethod
    def get_cleared_message(msg):
        clear_msg = msg.lower()
        clear_msg = clear_msg.replace(',', ' ')
        clear_msg = re.sub(" +", " ", clear_msg)
        clear_msg = clear_msg.strip().strip(',').strip().strip(' ').strip()
        clear_msg = clear_msg.replace('ё', 'е')
        return clear_msg

    def parse_from_payload(self, payload):
        self.command = payload.get('command')
        self.args = payload.get('args')
        self.args_str = " ".join(self.args)
        if self.args_str:
            self.raw = f"{self.command} {self.args_str}"
        else:
            self.raw = self.command
        self.clear = self.get_cleared_message(self.raw)
        self.id = None
