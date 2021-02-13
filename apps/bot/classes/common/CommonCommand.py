from apps.bot.classes.Consts import Role, ATTACHMENT_TRANSLATOR, Platform
from apps.bot.classes.Exceptions import PWarning, PError
from apps.bot.classes.bots.CommonBot import CommonBot
from apps.bot.classes.common.CommonMethods import get_help_for_command
from apps.bot.classes.events.Event import Event
from petrovich.settings import env


class CommonCommand:
    names: list or str = None  # Имена команды,
    help_text: str = None  # Текст в /команды
    detail_help_text: str = None  # Текст в детальной помощи по команде /помощь (название команды)
    keyboard = None  # Клавиатура для команды /клава
    access: Role = Role.USER  # Необходимые права для выполнения команды
    pm: bool = False  # Должно ли сообщение обрабатываться только в лс
    conversation: bool = False  # Должно ли сообщение обрабатываться только в конфе
    fwd: bool = False  # Должно ли сообщение обрабатываться только с пересланными сообщениями
    args: int = None  # Должно ли сообщение обрабатываться только с заданным количеством аргументов
    int_args: list = None  # Список аргументов, которые должны быть целым числом
    float_args: list = None  # Список аргументов, которые должны быть числом
    platforms: list or Platform = [Platform.VK, Platform.TG,  Platform.API, Platform.YANDEX]  # Список платформ, которые могут обрабатывать команду
    attachments: list = []  # Должно ли сообщение обрабатываться только с вложениями
    enabled: bool = True  # Включена ли команда
    priority: int = 0  # Приоритет обработки команды
    city: bool = False  # Должно ли сообщение обрабатываться только с заданным городом у пользователя
    suggest_for_similar: bool = True  # предлагать ли команду в выдаче похожих команд при ошибке пользователя в вводе

    def __init__(self):
        self.bot = None
        self.event = None

        if not isinstance(self.names, list):
            self.names = [self.names]
        if not isinstance(self.platforms, list):
            self.platforms = [self.platforms]

    def accept(self, event: Event):
        """
        Метод, определяющий на что среагирует команда. По умолчанию ищет команду в названиях
        :param event: событие
        :return: bool
        """
        if event.command in self.names:
            return True

        return False

    def check_and_start(self, bot: CommonBot, event: Event):
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
        :return:
        """
        # Если команда не для api
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
        if self.event.args:
            if len(self.event.args) >= args:
                return True
            else:
                error = "Передано недостаточно аргументов"
                error += f"\n\n{get_help_for_command(self)}"
                raise PWarning(error)

        error = "Для работы команды требуются аргументы"
        error += f"\n\n{get_help_for_command(self)}"
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

    @staticmethod
    def _transform_k(arg: str):
        """
        Перевод из строки с К в число. Пример: 1.3к = 1300
        :param arg: текстовое число с К
        :return: int
        """
        arg = arg.lower()
        count_m = arg.count('m') + arg.count('м')
        count_k = arg.count('k') + arg.count('к') + count_m * 2
        if count_k > 0:
            arg = arg \
                .replace('k', '') \
                .replace('к', '') \
                .replace('м', '') \
                .replace('m', '')
            arg = float(arg)
            arg *= 10 ** (3 * count_k)
        return arg

    def parse_int(self):
        """
        Парсинг аргументов в int из заданного диапазона индексов(self.int_args)
        :return: bool
        """
        if not self.event.args:
            return True
        for checked_arg_index in self.int_args:
            if len(self.event.args) - 1 >= checked_arg_index:
                if isinstance(self.event.args[checked_arg_index], int):
                    continue
                try:
                    self.event.args[checked_arg_index] = self._transform_k(self.event.args[checked_arg_index])
                    self.event.args[checked_arg_index] = int(self.event.args[checked_arg_index])
                except ValueError:
                    error = "Аргумент должен быть целочисленным"
                    raise PWarning(error)
        return True

    def parse_float(self):
        """
        Парсинг аргументов в float из заданного диапазона индексов(self.float_args)
        :return: bool
        """
        if not self.event.args:
            return True
        for checked_arg_index in self.float_args:
            if len(self.event.args) - 1 >= checked_arg_index:
                if isinstance(self.event.args[checked_arg_index], float):
                    continue
                try:
                    self.event.args[checked_arg_index] = self._transform_k(self.event.args[checked_arg_index])
                    self.event.args[checked_arg_index] = float(self.event.args[checked_arg_index])
                except ValueError:
                    error = "Аргумент должен быть с плавающей запятой"
                    raise PWarning(error)
        return True

    def check_pm(self):
        """
        Проверка на сообщение из ЛС
        :return: bool
        """
        if self.event.from_user:
            return True

        error = "Команда работает только в ЛС"
        raise PWarning(error)

    def check_conversation(self):
        """
        Проверка на сообщение из чата
        :return: bool
        """
        if self.event.from_chat:
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
                if att['type'] in self.attachments:
                    return True
        if self.event.fwd and self.event.fwd[0]['attachments']:
            for att in self.event.fwd[0]['attachments']:
                if att['type'] in self.attachments:
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
        raise PWarning(f"{self.detail_help_text}")
