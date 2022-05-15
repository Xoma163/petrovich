from apps.bot.classes.bots.Bot import Bot
from apps.bot.classes.consts.Consts import Role, ATTACHMENT_TRANSLATOR, Platform
from apps.bot.classes.consts.Exceptions import PWarning, PSkip, PIDK
from apps.bot.classes.events.Event import Event
from apps.bot.utils.utils import get_help_texts_for_command, transform_k


class Command:
    # Основные поля команды
    name: str = ""  # Имя команды,
    names: list = []  # Вспопогательные имена команды
    name_tg: str = ""  # Имя команды для списка команд в тг

    help_text: str = ""  # Текст в /команды
    help_texts: list = []  # Текст в детальной помощи по команде /помощь (название команды)
    help_texts_extra: str = ""  # Текст в детальной помощи по команде /помощь (название команды), который будет выводиться после основного текста

    enabled: bool = True  # Включена ли команда
    suggest_for_similar: bool = True  # предлагать ли команду в выдаче похожих команд при ошибке пользователя в вводе
    priority: int = 0  # Приоритет обработки команды
    hidden: bool = False  # Скрытая команда, будет отвечать пользователям без соответствующих прав заглушкой "я вас не понял"

    # Проверки
    access: Role = Role.USER  # Необходимые права для выполнения команды
    pm: bool = False  # Должно ли сообщение обрабатываться только в лс
    conversation: bool = False  # Должно ли сообщение обрабатываться только в конфе
    fwd: bool = False  # Должно ли сообщение обрабатываться только с пересланными сообщениями
    args: int = 0  # Должно ли сообщение обрабатываться только с заданным количеством аргументов
    args_or_fwd: int = None  # Должно ли сообщение обрабатываться только с пересланными сообщениями или аргументами
    int_args: list = []  # Список аргументов, которые должны быть целым числом
    float_args: list = []  # Список аргументов, которые должны быть числом
    platforms: list = list(Platform)  # Список платформ, которые могут обрабатывать команду
    excluded_platforms: list = []  # Список исключённых платформ.
    attachments: list = []  # Должно ли сообщение обрабатываться только с вложениями
    city: bool = False  # Должно ли сообщение обрабатываться только с заданным городом у пользователя
    mentioned: bool = False  # Должно ли сообщение обрабатываться только с упоминанием бота
    non_mentioned: bool = False  # Должно ли сообщение обрабатываться только без упоминания бота

    def __init__(self, bot: Bot = None, event: Event = None):
        self.bot: Bot = bot
        self.event: Event = event

        self.full_names: str = ""  # Полный список имён команды (основное имя, дополнительное, имя в тг)
        self.full_help_text: str = ""  # Сгенерированный хелп текст для команды /команды
        self.full_help_texts: str = ""  # Сгенерированный хелп текст для команды /помощь
        self.full_help_texts_tg: str = ""  # Сгенерированный хелп текст для списка команд в телеграме

        if self.name:
            self.full_names = [self.name] + self.names
            if self.help_text:
                self.full_help_text = f"{self.name.capitalize()} - {self.help_text}"
            if self.help_texts:
                self.full_help_texts = "\n".join([f"{self.name.capitalize()} {x}" for x in self.help_texts])
            if self.help_texts_extra:
                self.full_help_texts += f"\n{self.help_texts_extra}"
        if self.name_tg:
            self.full_names.append(self.name_tg)
            self.full_help_texts_tg = f"{self.name_tg.lower()} - {self.help_text}"

        if self.hidden:
            if self.suggest_for_similar:
                raise RuntimeError("Поле hidden=True и suggest_for_similar=True не могут быть вместе")
            if self.access == Role.USER:
                raise RuntimeError("Поле hidden=True и self.access=Role.USER не могут быть вместе")

    def __eq__(self, other):
        return self.name == other.name

    def accept(self, event: Event):
        """
        Метод, определяющий на что среагирует команда. По умолчанию ищет команду в названиях
        :param event: событие
        :return: bool
        """
        if event.command and event.command == self:
            return True
        if event.message and event.message.command in self.full_names:
            return True
        if event.payload and event.payload['command'] in self.full_names:
            return True
        return False

    @staticmethod
    def accept_extra(event):
        """
        Метод, определяющий нужно ли отреагировать команде вне обычных условий
        """

    def check_and_start(self, bot: Bot, event: Event):
        """
        Выполнение всех проверок и старт команды
        :param bot: сущность Bot
        :param event: сущность Event
        """
        self.bot = bot
        self.event = event

        self.checks()
        return self.start()

    def checks(self):
        """
        Проверки
        """
        self.check_platforms()
        self.check_sender(self.access)
        if self.pm:
            self.check_pm()
        if self.conversation:
            self.check_conversation()
        if self.fwd:
            self.check_fwd()
        if self.args:
            self.check_args()
        if self.args_or_fwd:
            self.check_args_or_fwd()
        if self.int_args:
            self.parse_int()
        if self.float_args:
            self.parse_float()
        if self.attachments:
            self.check_attachments()
        if self.city:
            self.check_city()
        if self.mentioned:
            self.check_mentioned()
        if self.non_mentioned:
            self.check_non_mentioned()

    def start(self):
        """
        Обработка самой команды
        :return: result (см. документацию)
        """
        raise NotImplementedError

    def check_sender(self, role: Role):
        """
        Проверка на роль отправителя
        :param role: требуемая роль
        :return: bool
        """
        if self.event.sender.check_role(role):
            return True
        if role == Role.CONFERENCE_ADMIN:
            if self.event.chat.admin == self.event.sender:
                return True
        if self.hidden:
            raise PIDK()
        error = f"Команда доступна только для пользователей с уровнем прав {role.value}"
        raise PWarning(error)

    def check_args(self, args: int = None):
        """
        Проверка на кол-во переданных аргументов
        :param args: количество требуемых аргументов
        :return: bool
        """
        if args is None or args == 0:
            args = self.args
        if self.event.message and self.event.message.args:
            if len(self.event.message.args) >= args:
                return True
            else:
                error = "Передано недостаточно аргументов"
                error += f"\n\n{get_help_texts_for_command(self, self.event.platform)}"
        else:
            error = "Для работы команды требуются аргументы"
        raise PWarning(error, keyboard=self._get_help_button_keyboard())

    def check_args_or_fwd(self, args: int = None):
        if args is None:
            args = self.args_or_fwd
        try:
            check_args = self.check_args(args)
        except Exception:
            check_args = False

        try:
            check_fwd = self.check_fwd()
        except Exception:
            check_fwd = False

        if check_args or check_fwd:
            return True

        error = "Для работы команды требуются аргументы или пересылаемые сообщения"
        error += f"\n\n{get_help_texts_for_command(self, self.event.platform)}"

        raise PWarning(error, keyboard=self._get_help_button_keyboard())

    @staticmethod
    def check_number_arg_range(arg, _min=-float('inf'), _max=float('inf'), banned_list: list = None):
        """
        Проверка на вхождение числа в диапазон и исключение его из заданного списка
        :param arg: число
        :param _min: мин. значение числа
        :param _max: макс. значение числа
        :param banned_list: список недопустимых значений
        :return: bool
        """
        if _min <= arg <= _max:
            if banned_list:
                if arg not in banned_list:
                    return True
                else:
                    error = f"Аргумент не может принимать значение {arg}"
                    raise PWarning(error)
            else:
                return True
        else:
            error = f"Значение может быть в диапазоне [{_min};{_max}]"
            raise PWarning(error)

    def parse_int(self):
        """
        Парсинг аргументов в int из заданного диапазона индексов(self.int_args)
        :return: bool
        """
        if not self.event.message.args:
            return True
        for checked_arg_index in self.int_args:
            if len(self.event.message.args) - 1 >= checked_arg_index:
                if isinstance(self.event.message.args[checked_arg_index], int):
                    continue
                try:
                    self.event.message.args[checked_arg_index] = transform_k(self.event.message.args[checked_arg_index])
                    self.event.message.args[checked_arg_index] = int(self.event.message.args[checked_arg_index])
                except ValueError:
                    error = "Аргумент должен быть целочисленным"
                    raise PWarning(error)
        return True

    def parse_float(self):
        """
        Парсинг аргументов в float из заданного диапазона индексов(self.float_args)
        :return: bool
        """
        if not self.event.message.args:
            return True
        for checked_arg_index in self.float_args:
            if len(self.event.message.args) - 1 >= checked_arg_index:
                if isinstance(self.event.message.args[checked_arg_index], float):
                    continue
                try:
                    self.event.message.args[checked_arg_index] = transform_k(self.event.message.args[checked_arg_index])
                    self.event.message.args[checked_arg_index] = float(self.event.message.args[checked_arg_index])
                except ValueError:
                    error = "Аргумент должен быть с плавающей запятой"
                    raise PWarning(error)
        return True

    def check_pm(self):
        """
        Проверка на сообщение из ЛС
        :return: bool
        """
        if self.event.is_from_pm:
            return True

        error = "Команда работает только в ЛС"
        raise PWarning(error)

    def check_conversation(self):
        """
        Проверка на сообщение из чата
        :return: bool
        """
        if self.event.is_from_chat:
            return True

        error = "Команда работает только в беседах"
        raise PWarning(error)

    def check_fwd(self):
        """
        Проверка на вложенные сообщения
        :return: bool
        """
        if self.event.fwd:
            return True

        error = "Перешлите сообщения"
        raise PWarning(error)

    def check_platforms(self):
        """
        Проверка на вид платформы
        :return: bool
        """
        if self.event.platform in self.excluded_platforms:
            error = f"Команда недоступна для {self.event.platform.value.upper()}"
            raise PWarning(error)
        if self.event.platform not in self.platforms:
            error = f"Команда недоступна для {self.event.platform.value.upper()}"
            raise PWarning(error)
        return True

    def check_attachments(self):
        """
        Проверка на вложения в сообщении или пересланных сообщениях
        :return: bool
        """
        if self.event.attachments:
            for att in self.event.attachments:
                if type(att) in self.attachments:
                    return True
        if self.event.fwd and self.event.fwd[0].attachments:
            for att in self.event.fwd[0].attachments:
                if type(att) in self.attachments:
                    return True

        allowed_types = ', '.join([ATTACHMENT_TRANSLATOR[_type] for _type in self.attachments])
        error = f"Для работы команды требуются вложения: {allowed_types}"
        raise PWarning(error)

    def check_city(self, city=None):
        """
        Проверяет на город у пользователя или в присланном сообщении
        :param city: город
        :return: bool
        """
        if city:
            return True
        if self.event.sender.city:
            return True

        error = "Не указан город в профиле. /профиль город (название) - устанавливает город пользователю"
        raise PWarning(error)

    def check_mentioned(self):
        """
        Проверяет на упоминание бота в сообщении
        :return: bool
        """
        if self.event.is_from_pm:
            return True
        if not self.event.message.mentioned:
            raise PSkip()
        return True

    def check_non_mentioned(self):
        if self.event.message.mentioned:
            raise PWarning("Команда работает только без упоминания")
        return True

    def handle_menu(self, menu: list, arg: str):
        """
        Вызов 'подпрограмм' основной команды по присланному аргументу
        :param menu: [[[keys1],[method1]],[[keys2],[method2]]]
        :param arg: переданный аргумент
        :return:
        """
        default_item = None
        for item in menu:
            if arg in item[0]:
                return item[1]
            if not default_item and 'default' in item[0]:
                default_item = item[1]
        if default_item:
            return default_item
        raise PWarning("Нет такого пункта меню", keyboard=self._get_help_button_keyboard())

    def _get_help_button_keyboard(self):
        button = self.bot.get_button(f"/помощь {self.name}", "помощь", [self.name])
        keyboard = self.bot.get_inline_keyboard([button])
        return keyboard

    def __eq__(self, another):
        return hasattr(another, 'data') and self.name == another.name

    def __hash__(self):
        return hash(self.name)
