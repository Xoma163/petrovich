from apps.bot.classes.bots.Bot import Bot
from apps.bot.classes.consts.Consts import Role, ATTACHMENT_TRANSLATOR, Platform
from apps.bot.classes.consts.Exceptions import PWarning, PError
from apps.bot.classes.events.Event import Event
from apps.bot.utils.utils import get_help_texts_for_command, transform_k
from petrovich.settings import env


class Command:
    # Основные поля команды
    name: str = None  # Имя команды,
    names: list = []  # Вспопогательные имена команды,
    help_text: str = None  # Текст в /команды
    help_texts: list = []  # Текст в детальной помощи по команде /помощь (название команды)
    enabled: bool = True  # Включена ли команда
    suggest_for_similar: bool = True  # предлагать ли команду в выдаче похожих команд при ошибке пользователя в вводе
    priority: int = 0  # Приоритет обработки команды

    # Проверки
    access: Role = Role.USER  # Необходимые права для выполнения команды
    pm: bool = False  # Должно ли сообщение обрабатываться только в лс
    conversation: bool = False  # Должно ли сообщение обрабатываться только в конфе
    fwd: bool = False  # Должно ли сообщение обрабатываться только с пересланными сообщениями
    args: int = None  # Должно ли сообщение обрабатываться только с заданным количеством аргументов
    args_or_fwd: int = None  # Должно ли сообщение обрабатываться только с пересланными сообщениями или аргументами
    int_args: list = None  # Список аргументов, которые должны быть целым числом
    float_args: list = None  # Список аргументов, которые должны быть числом
    platforms: list or Platform = list(Platform)  # Список платформ, которые могут обрабатывать команду ToDo: list only
    excluded_platforms: list = []  # Список исключённых платформ.
    attachments: list = []  # Должно ли сообщение обрабатываться только с вложениями
    city: bool = False  # Должно ли сообщение обрабатываться только с заданным городом у пользователя

    def __init__(self):
        self.bot: Bot = None
        self.event: Event = None

        if not isinstance(self.platforms, list):
            self.platforms = [self.platforms]

        # Дополнительные поля
        self.full_names = None
        self.full_help_text = None
        self.full_help_texts = None

        if self.name:
            self.full_names = [self.name] + self.names
            if self.help_text:
                self.full_help_text = f"{self.name.capitalize()} - {self.help_text}"
            if self.help_texts:
                self.full_help_texts = "\n".join([f"{self.name.capitalize()} {x}" for x in self.help_texts])

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
            if role == Role.ADMIN:
                if self.event.platform == Platform.VK:
                    if self.event.sender.user_id == env.str("VK_ADMIN_ID"):
                        return True
                    else:
                        print("Попытка доступа под админом не с моего id O_o")
                        raise PError("Э ты чё, ты не админ. Где мой админ???")
                elif self.event.platform == Platform.TG:
                    if self.event.sender.user_id == env.str("TG_ADMIN_ID"):
                        return True
                    else:
                        print("Попытка доступа под админом не с моего id O_o")
                        raise PError("Э ты чё, ты не админ. Где мой админ???")
            else:
                return True
        if role == Role.CONFERENCE_ADMIN:
            if self.event.chat.admin == self.event.sender:
                return True
        error = f"Команда доступна только для пользователей с уровнем прав {role.value}"
        raise PWarning(error)

    def check_args(self, args: int = None):
        """
        Проверка на кол-во переданных аргументов
        :param args: количество требуемых аргументов
        :return: bool
        """
        if args is None:
            args = self.args
        if self.event.message.args:
            if len(self.event.message.args) >= args:
                return True
            else:
                error = "Передано недостаточно аргументов"
                error += f"\n\n{get_help_texts_for_command(self)}"
                raise PWarning(error)

        error = "Для работы команды требуются аргументы"
        error += f"\n\n{get_help_texts_for_command(self)}"
        raise PWarning(error)

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
        error += f"\n\n{get_help_texts_for_command(self)}"
        raise PWarning(error)

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

        allowed_types = ' '.join([ATTACHMENT_TRANSLATOR[_type] for _type in self.attachments])
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
        # raise PWarning(f"{self.help_texts}")
        raise PWarning(get_help_texts_for_command(self))
