import copy
import re


class Message:
    COMMAND_SYMBOLS = ['/', '!']
    KEYS_SYMBOL = "—"
    KEYS_STR = "--"
    SPACE_REGEX = r' |\n'

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
        self.has_mention = False

        self.raw = ""
        self.command = ""
        self.clear = ""
        self.clear_case = ""

        # Аргументы
        self.args_str = ""
        self.args = []
        self.args_str_case = ""
        self.args_case = []

        # Кварги с клавиатур
        self.kwargs = {}

        # Ключи
        self.keys = []

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
        msg_split = re.split(self.SPACE_REGEX, self.clear, 1)
        self.command = msg_split[0]

        new_msg_split = []
        for item in msg_split:
            if item.startswith(self.KEYS_STR):
                self.keys.append(item[2:])
                continue
            if item.startswith(self.KEYS_SYMBOL):
                self.keys.append(item[1:])
                continue
            new_msg_split.append(item)
        msg_split = new_msg_split

        if len(msg_split) > 1:
            self.args_str = msg_split[1]
            self.args = re.split(self.SPACE_REGEX, self.args_str)

        # case
        self.clear_case = clear_message
        self.args_str_case = None
        self.args_case = None

        msg_case_split = re.split(self.SPACE_REGEX, clear_message, 1)

        if len(msg_case_split) > 1:
            self.args_str_case = msg_case_split[1]
            self.args_case = re.split(self.SPACE_REGEX, self.args_str_case)

    @staticmethod
    def get_cleared_message(msg) -> str:
        clear_msg = re.sub(" +", " ", msg)
        clear_msg = re.sub(",+", ",", clear_msg)
        clear_msg = clear_msg.strip().strip(',').strip().strip(' ').strip()
        clear_msg = clear_msg.replace('ё', 'е').replace("Ё", 'Е')
        return clear_msg

    def parse_from_payload(self, payload):
        command = payload.get("c")
        args = payload.get("a")
        self.kwargs = payload.get("k")
        raw = command
        if args:
            if isinstance(args, str):
                raw += f" {args}"
            else:
                args = [str(x) for x in args]
                raw += f" {' '.join(args)}"
        self.parse_raw(raw)

    @property
    def mentioned(self) -> bool:
        return self.has_command_symbols or self.has_mention

    def to_log(self) -> dict:
        dict_self = copy.copy(self.__dict__)
        return dict_self
