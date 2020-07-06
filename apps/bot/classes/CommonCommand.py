from datetime import datetime

from apps.bot.classes.CommonMethods import check_user_group, get_help_for_command, remove_tz
from apps.bot.classes.Consts import Role
from apps.service.models import Service
from petrovich.settings import env


class CommonCommand:
    """
    # names - Имена, на которые откликается команда
        help_text - Текст в помощи
        keyboard - Клавиатура
        access - Команда для ?
        pm - Команда для лс
        conversation - Команда для конф
        fwd - Требуются пересылаемые сообщения
        args - Требуются аргументы(число)
        int_args - Требуются интовые аргументы (позиции)
        api - Работает ли команда для api
    """

    def __init__(self,
                 names,
                 help_text=None,
                 detail_help_text=None,
                 keyboard=None,
                 access=None,
                 pm=False,
                 conversation=False,
                 fwd=False,
                 args=None,
                 int_args=None,
                 float_args=None,
                 api=None,
                 tg=None,
                 attachments=False,
                 enabled=True,
                 priority=0,
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
        self.api = api
        self.tg = tg
        self.attachments = attachments
        self.enabled = enabled
        self.priority = priority

        self.vk_bot = None
        self.vk_event = None

    # Метод, определяющий на что среагирует команда
    def accept(self, vk_event):
        if vk_event.command in self.names:
            return True

        return False

    # Выполнение всех проверок и старт команды
    def check_and_start(self, vk_bot, vk_event):
        self.vk_bot = vk_bot
        self.vk_event = vk_event

        self.checks()
        return self.start()

    # Проверки
    def checks(self):
        # Если команда не для api
        self.check_api()
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

    def start(self):
        pass

    # Проверяет роль отправителя
    def check_sender(self, role):
        if check_user_group(self.vk_event.sender, role):
            if role == Role.ADMIN:
                if self.vk_event.sender.user_id == env.str("VK_ADMIN_ID"):
                    return True
                else:
                    print("Попытка доступа под админом не с моего id O_o")
            else:
                return True
        if role == Role.CONFERENCE_ADMIN:
            if self.vk_event.chat.admin == self.vk_event.sender:
                return True
        error = f"Команда доступна только для пользователей с уровнем прав {role.value}"
        raise RuntimeError(error)

    # Проверяет количество переданных аргументов
    def check_args(self, args=None):
        if args is None:
            args = self.args
        if self.vk_event.args:
            if len(self.vk_event.args) >= args:
                return True
            else:
                error = "Передано недостаточно аргументов"
                error += f"\n\n{get_help_for_command(self)}"
                raise RuntimeError(error)

        error = "Для работы команды требуются аргументы"
        error += f"\n\n{get_help_for_command(self)}"
        raise RuntimeError(error)

    # Проверяет интовый аргумент в диапазоне
    @staticmethod
    def check_number_arg_range(arg, val1, val2, banned_list=None):
        if val1 <= arg <= val2:
            if banned_list:
                if arg not in banned_list:
                    return True
                else:
                    error = f"Аргумент не может принимать значение {arg}"
                    raise RuntimeError(error)
            else:
                return True
        else:
            error = f"Значение может быть в диапазоне [{val1};{val2}]"
            raise RuntimeError(error)

    @staticmethod
    def _transform_k(arg):
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

    # Парсит аргументы в тип int
    def parse_int(self):
        if not self.vk_event.args:
            return True
        for checked_arg_index in self.int_args:
            if len(self.vk_event.args) - 1 >= checked_arg_index:
                if isinstance(self.vk_event.args[checked_arg_index], int):
                    continue
                try:
                    self.vk_event.args[checked_arg_index] = self._transform_k(self.vk_event.args[checked_arg_index])
                    self.vk_event.args[checked_arg_index] = int(self.vk_event.args[checked_arg_index])
                except ValueError:
                    error = "Аргумент должен быть целочисленным"
                    raise RuntimeError(error)
        return True

    # Парсит аргументы в тип float
    def parse_float(self):
        if not self.vk_event.args:
            return True
        for checked_arg_index in self.float_args:
            if len(self.vk_event.args) - 1 >= checked_arg_index:
                if isinstance(self.vk_event.args[checked_arg_index], float):
                    continue
                try:
                    self.vk_event.args[checked_arg_index] = self._transform_k(self.vk_event.args[checked_arg_index])
                    self.vk_event.args[checked_arg_index] = float(self.vk_event.args[checked_arg_index])
                except ValueError:
                    error = "Аргумент должен быть с плавающей запятой"
                    raise RuntimeError(error)
        return True

    # Проверяет, прислано ли сообщение в лс
    def check_pm(self):
        if self.vk_event.from_user:
            return True

        error = "Команда работает только в ЛС"
        raise RuntimeError(error)

    # Проверяет, прислано ли пересланное сообщение
    def check_fwd(self):
        if self.vk_event.fwd:
            return True

        error = "Перешлите сообщения"
        raise RuntimeError(error)

    # Проверяет, прислано ли сообщение в чат
    def check_conversation(self):
        if self.vk_event.from_chat:
            return True

        error = "Команда работает только в беседах"
        raise RuntimeError(error)

    # Проверяет, прошло ли время с последнего выполнения команды и можно ли выполнять команду
    @staticmethod
    def check_command_time(name, seconds):
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

    # Проверяет, прислано ли сообщение через API
    def check_api(self):
        # Если запрос пришёл через api
        if self.vk_event.from_api:
            if self.api == False:
                error = "Команда недоступна для API"
                raise RuntimeError(error)

        if not self.vk_event.from_api:
            if self.api:
                error = "Команда недоступна для VK"
                raise RuntimeError(error)

        return True

    # ToDo: check on types
    def check_attachments(self, types=None):
        if self.vk_event.attachments:
            if types:
                pass
            return True

        error = "Пришлите вложения"
        raise RuntimeError(error)

    # example:
    # [[[key1],[method1]],[[key2],[method2]]]
    def handle_menu(self, menu, arg):
        default_item = None
        for item in menu:
            if arg in item[0]:
                return item[1]
            if not default_item and 'default' in item[0]:
                default_item = item[1]
        if default_item:
            return default_item
        raise RuntimeWarning(f"{self.detail_help_text}")
