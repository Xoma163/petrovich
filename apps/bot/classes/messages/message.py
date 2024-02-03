import re


class Message:
    COMMAND_SYMBOLS = ['/']
    KEYS_SYMBOLS = ["—", "--"]
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

        self.has_command_symbols: bool = False
        self.has_mention: bool = False

        self.raw: str = ""
        self.command: str = ""
        self.clear: str = ""
        self.clear_case: str = ""

        # Аргументы
        self.args_str: str = ""
        self.args: list = []
        self.args_str_case: str = ""
        self.args_case: list = []

        # Кварги с клавиатур
        self.kwargs: dict = {}

        # Ключи
        self.keys: list = []

        self.id = _id

        # Выделенное сообщение пользователя
        self.quote: str = ""

        if not raw_str:
            return

        self.parse_raw(raw_str)

    def parse_raw(self, raw_str):
        self.raw = raw_str
        if not self.raw:
            return

        if self.raw[0] in self.COMMAND_SYMBOLS:
            self.has_command_symbols = True
            raw_str = raw_str[1:]

        self.clear_case = self.get_cleared_message(raw_str)
        self.clear = self.clear_case.lower()

        msg_split = re.split(self.SPACE_REGEX, self.clear_case, 1)

        self.command = msg_split[0].lower()

        # Нет аргументов - выходим
        if len(msg_split) == 1:
            return

        args_str = msg_split[1]

        new_args_split = []
        args_split = re.split(self.SPACE_REGEX, args_str)
        # Проставление ключей, удаление их из строки, пропуск пустых аргументов
        for arg in args_split:
            if not arg:
                continue
            key = None
            for key_symbol in self.KEYS_SYMBOLS:
                if arg.startswith(key_symbol):
                    key = arg[len(key_symbol):].lower()
                    break
            if key:
                index = args_str.find(arg)
                self.keys.append(key)

                if index == 0:
                    args_str = args_str[:index]
                    continue
                elif index != -1:
                    args_str = args_str[:index - 1] + args_str[index + len(arg):]
                    continue
            new_args_split.append(arg)

        # Нет аргументов - выходим
        if len(new_args_split) == 0:
            return
        self.args_str_case = args_str
        self.args_str = args_str.lower()
        self.args_case = new_args_split
        self.args = [x.lower() for x in self.args_case]

    @staticmethod
    def get_cleared_message(msg) -> str:
        clear_msg = re.sub(" +", " ", msg)
        clear_msg = re.sub("\n+", "\n", clear_msg)
        clear_msg = clear_msg.strip().strip(',').strip().strip(' ').strip().strip('\n').strip()
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
        return {
            'id': self.id,
            'raw': self.raw,
            'command': self.command,
            'args_str': self.args_str,
            'keys': self.keys,
            'kwargs': self.kwargs
        }
