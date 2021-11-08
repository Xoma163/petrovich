from django.contrib.auth.models import Group

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import ON_OFF_TRANSLATOR, Role, TRUE_FALSE_TRANSLATOR, Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.models import User


class Settings(Command):
    name = "настройки"
    names = ["настройка"]
    name_tg = 'settings'

    help_text = "устанавливает некоторые настройки пользователя/чата"
    help_texts = [
        "- присылает текущие настройки",
        "(настройка) (вкл/выкл) - устанавливает некоторые настройки пользователя/чата",
        "упоминание (вкл/выкл) - определяет будет ли бот триггериться на команды без упоминания в конфе(требуются админские права)",
        "реагировать (вкл/выкл) - определяет, будет ли бот реагировать на неправильные команды в конфе. Это сделано для того, чтобы в конфе с несколькими ботами не было ложных срабатываний",
        "мемы (вкл/выкл) - определяет, будет ли бот присылать мем если прислано его точное название без / (боту требуется доступ к переписке)",
        "туррет (вкл/выкл) - определяет, будет ли бот иногда ругаться)",
        "голосовые (вкл/выкл) - определяет, будет ли бот автоматически распознавать голосовые",
        "майнкрафт (вкл/выкл) - определяет, будет ли бот присылать информацию о серверах майна. (для доверенных)",
        "др (вкл/выкл) - определяет, будет ли бот поздравлять с Днём рождения и будет ли ДР отображаться в /профиль"
        "платформа (вк/vk/тг/tg) - определяет платформу по умолчанию для важных писем от бота. По умолчанию первая платформа с которой вы написали боту"
    ]

    def start(self):
        if self.event.message.args:
            arg0 = self.event.message.args[0]
        else:
            arg0 = None

        menu = [
            [['реагировать', 'реагируй', 'реагирование'], self.menu_reaction],
            [['упоминание', 'упоминания', 'триггериться', 'тригериться'], self.menu_mentioning],
            [['майнкрафт', 'майн', 'minecraft', 'mine'], self.menu_minecraft_notify],
            [['мемы', 'мем'], self.menu_memes],
            [['др', 'днюха'], self.menu_bd],
            [['платформа'], self.menu_platform],
            [['голосовые', 'голос', 'голосовухи', 'голосовуха', 'голосовое'], self.menu_voice],
            [['туррет'], self.menu_turret],
            [['default'], self.menu_default],
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    @staticmethod
    def get_on_or_off(arg):
        if arg in ON_OFF_TRANSLATOR:
            return ON_OFF_TRANSLATOR[arg]
        else:
            raise PWarning("Не понял, включить или выключить?")

    def menu_reaction(self):
        return self.setup_default_chat_setting('need_reaction')

    def menu_mentioning(self):
        return self.setup_default_chat_setting('mentioning')

    def menu_memes(self):
        return self.setup_default_chat_setting('need_meme')

    def menu_bd(self):
        self.check_args(2)
        value = self.get_on_or_off(self.event.message.args[1])
        self.event.sender.celebrate_bday = value
        self.event.sender.save()
        return "Сохранил настройку"

    def menu_platform(self):
        self.check_args(2)
        value = self.event.message.args[1]
        if value in ['vk', 'вк', 'вконтакте']:
            platform = Platform.VK
        elif value in ['tg', 'тг', 'телеграм', 'телега', 'телеграмм']:
            platform = Platform.TG
        else:
            raise PWarning(f"Я не знаю платформы {self.event.message.args[1]}")

        try:
            self.event.sender.get_user_by_platform(platform)
        except User.DoesNotExist:
            raise PWarning("У вас нет пользователя в этой платформе")

        self.event.sender.default_platform = platform.name
        self.event.sender.save()

        return f"Поменял платформу на {platform.name}"

    def menu_minecraft_notify(self):
        self.check_sender(Role.TRUSTED)
        self.check_args(2)

        value = self.get_on_or_off(self.event.message.args[1])

        group_minecraft_notify = Group.objects.get(name=Role.MINECRAFT_NOTIFY.name)
        if value:
            self.event.sender.groups.add(group_minecraft_notify)
            self.event.sender.save()
            return "Подписал на рассылку о сервере майна"
        else:
            self.event.sender.groups.remove(group_minecraft_notify)
            self.event.sender.save()
            return "Отписал от рассылки о сервере майна"

    def menu_voice(self):
        return self.setup_default_chat_setting('recognize_voice')

    def menu_turret(self):
        self.check_sender(Role.CONFERENCE_ADMIN)
        self.check_args(2)

        value = self.get_on_or_off(self.event.message.args[1])
        self.event.chat.need_turret = value
        self.event.chat.save()
        return "Сохранил настройку"

    def menu_default(self):
        msg = ""
        if self.event.chat:
            msg = "Настройки чата:\n"

            reaction = self.event.chat.need_reaction
            need_meme = self.event.chat.need_meme
            mentioning = self.event.chat.mentioning
            turret = self.event.chat.need_turret
            recognize_voice = self.event.chat.recognize_voice

            msg += f"Реагировать на неправильные команды - {TRUE_FALSE_TRANSLATOR[reaction]}\n"
            msg += f"Присылать мемы по точным названиям - {TRUE_FALSE_TRANSLATOR[need_meme]}\n"
            msg += f"Триггериться на команды без упоминания - {TRUE_FALSE_TRANSLATOR[mentioning]}\n"
            msg += f"Автоматически распознавать голосовые - {TRUE_FALSE_TRANSLATOR[recognize_voice]}\n"
            msg += f"Синдром Туррета - {TRUE_FALSE_TRANSLATOR[turret]}\n"

            msg += "\n"

        msg += "Настройки пользователя:\n"

        if self.event.sender.check_role(Role.TRUSTED):
            minecraft_notify = self.event.sender.check_role(Role.MINECRAFT_NOTIFY)
            msg += f"Уведомления по майну - {TRUE_FALSE_TRANSLATOR[minecraft_notify]}\n"
        celebrate_bday = self.event.sender.celebrate_bday
        default_platform = self.event.sender.default_platform
        msg += f"Поздравлять с днём рождения - {TRUE_FALSE_TRANSLATOR[celebrate_bday]}\n"
        msg += f"Платформа по умолчанию - {default_platform}"
        return msg

    def setup_default_chat_setting(self, name):
        self.check_conversation()
        self.check_sender(Role.CONFERENCE_ADMIN)
        self.check_args(2)

        value = self.get_on_or_off(self.event.message.args[1])
        setattr(self.event.chat, name, value)
        self.event.chat.save()
        return "Сохранил настройку"
