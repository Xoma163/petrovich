from datetime import datetime

from apps.bot.classes.Consts import Role, ATTACHMENT_TRANSLATOR
from apps.bot.classes.common.CommonMethods import check_user_group, get_help_for_command, remove_tz
from apps.service.models import Service
from petrovich.settings import env


class CommonCommand:
    """
    names: Имена команды,
    help_text: Текст в /команды,
    detail_help_text: Текст в детальной помощи по команде /помощь (название команды),
    keyboard: Клавиатура для команды /клава
    access: Необходимые права для выполнения команды
    pm: Должно ли сообщение обрабатываться только в лс
    conversation: Должно ли сообщение обрабатываться только в конфе
    fwd: Должно ли сообщение обрабатываться только с пересланными сообщениями
    args: Должно ли сообщение обрабатываться только с заданным количеством аргументов
    int_args: Список аргументов, которые должны быть целым числом
    float_args: Список аргументов, которые должны быть числом
    platforms: Список платформ, которые могут обрабатывать команду
    attachments: Должно ли сообщение обрабатываться только с вложениями
    enabled: Включена ли команда
    priority: Приоритет обработки команды
    city: Должно ли сообщение обрабатываться только с заданным городом у пользователя
    """

    def __init__(self,
                 names: list,
                 help_text: str = None,
                 detail_help_text: str = None,
                 keyboard=None,
                 access: Role = None,
                 pm: bool = False,
                 conversation: bool = False,
                 fwd: bool = False,
                 args: int = None,
                 int_args: list = None,
                 float_args: list = None,
                 platforms: list = None,
                 attachments: list = False,
                 enabled: bool = True,
                 priority: int = 0,
                 city: bool = False,
                 ):
        self.names = names
        self.help_text = help_text
        self.detail_help_text = detail_help_text
        self.keyboard = keyboard
        self.access = access or Role.USER
        self.pm = pm
        self.conversation = conversation
        self.fwd = fwd
        self.args = args
        self.int_args = int_args
        self.float_args = float_args
        self.platforms = platforms or ['vk', 'tg', 'api']
        self.attachments = attachments
        self.enabled = enabled
        self.priority = priority
        self.city = city

        self.bot = None
        self.event = None

    def accept(self, event):
        """
        Метод, определяющий на что среагирует команда. По умолчанию ищет команду в названиях
        :param event: событие
        :return: bool
        """
        if event.command in self.names:
            return True

        return False

    def check_and_start(self, bot, event):
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
        raise NotImplemented()

    def check_sender(self, role):
        """
        Проверка на роль отправителя
        :param role: требуемая роль
        :return: bool
        """
        if check_user_group(self.event.sender, role):
            if role == Role.ADMIN:
                if self.event.platform == 'vk':
                    if self.event.sender.user_id == env.str("VK_ADMIN_ID"):
                        return True
                elif self.event.platform == 'tg':
                    if self.event.sender.user_id == env.str("TG_ADMIN_ID"):
                        return True
                else:
                    print("Попытка доступа под админом не с моего id O_o")
            else:
                return True
        if role == Role.CONFERENCE_ADMIN:
            if self.event.chat.admin == self.event.sender:
                return True
        error = f"Команда доступна только для пользователей с уровнем прав {role.value}"
        raise RuntimeError(error)

    def check_args(self, args=None):
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
                raise RuntimeError(error)

        error = "Для работы команды требуются аргументы"
        error += f"\n\n{get_help_for_command(self)}"
        raise RuntimeWarning(error)

    @staticmethod
    def check_number_arg_range(arg, _min, _max, banned_list=None):
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
                    raise RuntimeError(error)
            else:
                return True
        else:
            error = f"Значение может быть в диапазоне [{_min};{_max}]"
            raise RuntimeError(error)

    @staticmethod
    def _transform_k(arg):
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
                    raise RuntimeError(error)
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
                    raise RuntimeError(error)
        return True

    def check_pm(self):
        """
        Проверка на сообщение из ЛС
        :return: bool
        """
        if self.event.from_user:
            return True

        error = "Команда работает только в ЛС"
        raise RuntimeError(error)

    def check_conversation(self):
        """
        Проверка на сообщение из чата
        :return: bool
        """
        if self.event.from_chat:
            return True

        error = "Команда работает только в беседах"
        raise RuntimeError(error)

    def check_fwd(self):
        """
        Проверка на вложенные сообщения
        :return: bool
        """
        if self.event.fwd:
            return True

        error = "Перешлите сообщения"
        raise RuntimeError(error)

    @staticmethod
    def check_command_time(name, seconds):
        """
        Проверка на то, прошло ли время с последнего выполнения команды и можно ли выполнять команду
        :param name: название команды
        :param seconds: количество времени, после которого разрешается повторно выполнить команду
        :return: bool
        """
        entity, created = Service.objects.get_or_create(name=name)
        if created:
            return True
        update_datetime = entity.update_datetime
        delta_time = datetime.utcnow() - remove_tz(update_datetime)
        if delta_time.seconds < seconds and delta_time.days == 0:
            error = f"Нельзя часто вызывать данную команду. Осталось {seconds - delta_time.seconds} секунд"
            raise RuntimeError(error)
        entity.name = name
        entity.save()
        return True

    def check_platforms(self):
        """
        Проверка на вид платформы
        :return: bool
        """
        if self.event.platform not in self.platforms:
            error = f"Команда недоступна для {self.event.platform.upper()}"
            raise RuntimeError(error)
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
        raise RuntimeError(error)

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

        error = "Не указан город в профиле. /город (название) - устанавливает город пользователю"
        raise RuntimeError(error)

    def handle_menu(self, menu, arg):
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
        raise RuntimeWarning(f"{self.detail_help_text}")
