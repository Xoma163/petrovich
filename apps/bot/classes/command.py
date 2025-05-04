from apps.bot.classes.bots.bot import Bot
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning, PSkip, PIDK
from apps.bot.classes.event.event import Event
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.attachments.audio import AudioAttachment
from apps.bot.classes.messages.attachments.document import DocumentAttachment
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.attachments.sticker import StickerAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.attachments.video_note import VideoNoteAttachment
from apps.bot.classes.messages.attachments.voice import VoiceAttachment
from apps.bot.classes.messages.response_message import ResponseMessage
from apps.bot.utils.utils import get_help_texts_for_command, transform_k


class Command:
    # Основные поля команды
    name: str = ""  # Имя команды
    names: list = []  # Вспопогательные имена команды

    help_text: HelpText | None = None  # текст для команды /команды и для /помощь

    enabled: bool = True  # Включена ли команда
    suggest_for_similar: bool = True  # предлагать ли команду в выдаче похожих команд при ошибке пользователя в вводе
    priority: int = 0  # Приоритет обработки команды
    hidden: bool = False  # Скрытая команда, будет отвечать пользователям без соответствующих прав заглушкой "я вас не понял"

    abstract: bool = False  # Абстрактная команда, которая не запускается и не попадает в список всех команд

    # Проверки
    access: Role = Role.USER  # Необходимые права для выполнения команды
    pm: bool = False  # Должно ли сообщение обрабатываться только в лс
    conversation: bool = False  # Должно ли сообщение обрабатываться только в конфе
    fwd: bool = False  # Должно ли сообщение обрабатываться только с пересланными сообщениями
    args: int = 0  # Должно ли сообщение обрабатываться только с заданным количеством аргументов
    args_or_fwd: bool = False  # Должно ли сообщение обрабатываться только с пересланными сообщениями или аргументами
    int_args: list = []  # Список аргументов, которые должны быть целым числом
    float_args: list = []  # Список аргументов, которые должны быть числом
    platforms: list = list(Platform)  # Список платформ, которые могут обрабатывать команду
    excluded_platforms: list = []  # Список исключённых платформ.
    attachments: list = []  # Должно ли сообщение обрабатываться только с вложениями
    city: bool = False  # Должно ли сообщение обрабатываться только с заданным городом у пользователя
    mentioned: bool = False  # Должно ли сообщение обрабатываться только с упоминанием бота
    non_mentioned: bool = False  # Должно ли сообщение обрабатываться только без упоминания бота

    ATTACHMENT_TRANSLATOR = {
        AudioAttachment: 'аудио',
        VideoAttachment: 'видео',
        PhotoAttachment: 'фото',
        DocumentAttachment: 'документ',
        VoiceAttachment: 'голосовое',
        StickerAttachment: 'стикер',
        VideoNoteAttachment: 'кружочек',
        LinkAttachment: 'ссылка'
    }

    def __init__(self, bot: Bot = None, event: Event = None):
        self.bot: Bot = bot
        self.event: Event = event

        self.full_names: str = ""  # Полный список имён команды (основное имя, дополнительное, имя в тг)

        if self.name:
            self.full_names = [self.name] + self.names

        if self.hidden and self.suggest_for_similar:
            raise RuntimeError("Поле hidden=True и suggest_for_similar=True не могут быть переданы вместе")

    def accept(self, event: Event) -> bool:
        """
        Метод, определяющий на что среагирует команда. По умолчанию ищет команду в названиях
        :param event: событие
        :return: bool
        """
        if self.full_names:
            if event.message.command in self.full_names:
                return True
            if event.payload and event.payload['c'] in self.full_names:
                return True
        return False

    def check_and_start(self, bot: Bot, event: Event) -> ResponseMessage:
        """
        Выполнение всех проверок и старт команды
        :param bot: сущность Bot
        :param event: сущность Event
        """
        self.bot = bot
        self.event = event

        self.checks()
        rm = self.start()

        if not rm:
            rm = ResponseMessage()

        # Установка peer_id и message_thread_id по умолчанию, чтобы не писать в каждой команде
        # Если нужно указать другой peer_id и message_thread_id, то нужно указать это явно
        for rm_message in rm.messages:
            if rm_message.peer_id is None:
                rm_message.peer_id = event.peer_id
            if rm_message.message_thread_id is None:
                rm_message.message_thread_id = event.message_thread_id

        return rm

    def checks(self):
        """
        Проверки
        """
        if self.event.action:
            return
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

    def start(self) -> ResponseMessage | None:
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
            return
        if self.hidden:
            raise PIDK()
        error = f"Команда доступна только для пользователей с уровнем прав {role}"
        raise PWarning(error)

    def check_args(self, args: int = None) -> bool:
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
                error += f"\n\n{get_help_texts_for_command(self)}"
        else:
            error = "Для работы команды требуются аргументы"
        raise PWarning(error, keyboard=self._get_help_button_keyboard())

    def check_args_or_fwd(self, args: int = None) -> bool:
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
                    return
                else:
                    error = f"Аргумент не может принимать значение {arg}"
                    raise PWarning(error)
            else:
                return
        else:
            error = f"Значение может быть в диапазоне [{_min};{_max}]"
            raise PWarning(error)

    def parse_int(self):
        """
        Парсинг аргументов в int из заданного диапазона индексов(self.int_args)
        :return: bool
        """
        if not self.event.message.args:
            return
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

    def parse_float(self):
        """
        Парсинг аргументов в float из заданного диапазона индексов(self.float_args)
        :return: bool
        """
        if not self.event.message.args:
            return
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

    def check_pm(self) -> bool:
        """
        Проверка на сообщение из ЛС
        :return: bool
        """
        if self.event.is_from_pm:
            return True

        error = "Команда работает только в ЛС"
        raise PWarning(error)

    def check_conversation(self) -> bool:
        """
        Проверка на сообщение из чата
        :return: bool
        """
        if self.event.is_from_chat:
            return True

        error = "Команда работает только в беседах"
        raise PWarning(error)

    def check_fwd(self) -> bool:
        """
        Проверка на вложенные сообщения
        :return: bool
        """
        if self.event.fwd:
            return True

        error = "Перешлите сообщения"
        raise PWarning(error)

    def check_platforms(self) -> bool:
        """
        Проверка на вид платформы
        :return: bool
        """
        if self.event.platform in self.excluded_platforms:
            error = f"Команда недоступна для {self.event.platform.upper()}"
            raise PWarning(error)
        if self.event.platform not in self.platforms:
            error = f"Команда недоступна для {self.event.platform.upper()}"
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
                    return
        if self.event.fwd and self.event.fwd[0].attachments:
            for att in self.event.fwd[0].attachments:
                if type(att) in self.attachments:
                    return

        allowed_types = ', '.join([self.ATTACHMENT_TRANSLATOR[_type] for _type in self.attachments])
        error = f"Для работы команды требуются вложения: {allowed_types}"
        raise PWarning(error)

    def check_city(self, city=None):
        """
        Проверяет на город у пользователя или в присланном сообщении
        :param city: город
        :return: bool
        """
        if city:
            return
        if self.event.sender.city:
            return

        error = "Не указан город в профиле. /профиль город (название) - устанавливает город пользователю"
        raise PWarning(error)

    def check_mentioned(self):
        """
        Проверяет на упоминание бота в сообщении
        :return: bool
        """
        if self.event.is_from_pm:
            return
        if self.event.payload and self.event.payload.get('c') in self.full_names:
            return
        if not self.event.message.mentioned:
            raise PSkip()

    def check_non_mentioned(self) -> bool:
        """
        Проверяет на отсутствие упоминания бота в сообщении
        """
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

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name


class AcceptExtraMixin(Command):
    @staticmethod
    def accept_extra(event):
        """
        Метод, определяющий нужно ли отреагировать команде вне обычных условий
        """
        raise NotImplementedError
