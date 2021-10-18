import copy
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

        clear_case - произведены замены ',' на пробел, ё->е
        args_case - аргументы с учётом регистра списком
        args_str_case - аргументы с учётом регистра строкой

        """
        self.has_command_symbols = False

        self.raw = ""
        self.command = ""
        self.clear = ""
        self.clear_case = ""
        self.args_str = ""
        self.args = []
        self.args_str_case = ""
        self.args_case = []
        self.id = _id

        if not raw_str:
            return

        self.parse_raw(raw_str)

    def parse_raw(self, raw_str):
        self.raw = raw_str

        if self.raw[0] in self.COMMAND_SYMBOLS:
            self.has_command_symbols = True
            raw_str = raw_str[1:]

        clear_message = self.get_cleared_message(raw_str)

        # No case
        self.clear = clear_message.lower()
        msg_split = self.clear.split(' ', 1)
        self.command = msg_split[0]
        if len(msg_split) > 1:
            self.args_str = msg_split[1]
            self.args = self.args_str.split(' ')

        # case
        self.clear_case = clear_message
        msg_case_split = clear_message.split(' ', 1)
        self.args_str_case = None
        self.args_case = None
        if len(msg_case_split) > 1:
            self.args_str_case = msg_case_split[1]
            self.args_case = self.args_str_case.split(' ')

    @staticmethod
    def get_cleared_message(msg):
        clear_msg = msg.replace(',', ' ')
        clear_msg = re.sub(" +", " ", clear_msg)
        clear_msg = clear_msg.strip().strip(',').strip().strip(' ').strip()
        clear_msg = clear_msg.replace('ё', 'е').replace("Ё", 'Е')
        return clear_msg

    def parse_from_payload(self, payload):
        command = payload.get('command')
        args = payload.get('args')
        raw = command
        if args:
            args = [str(x) for x in args]
            raw += f" {' '.join(args)}"
        self.parse_raw(raw)

    def to_log(self):
        dict_self = copy.copy(self.__dict__)
        return dict_self
