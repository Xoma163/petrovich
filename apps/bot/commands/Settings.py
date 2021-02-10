from django.contrib.auth.models import Group

from apps.bot.classes.Consts import ON_OFF_TRANSLATOR, Role, TRUE_FALSE_TRANSLATOR
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.common.CommonCommand import CommonCommand


class Settings(CommonCommand):
    names = ["настройки", "настройка"]
    help_text = "Настройки - устанавливает некоторые настройки пользователя/чата"
    detail_help_text = \
        "Настройки (настройка) (вкл/выкл) - устанавливает некоторые настройки пользователя/чата\n" \
        "Настройки реагировать (вкл/выкл) - определяет, будет ли бот реагировать на неправильные команды в конфе. " \
        "Это сделано для того, чтобы в конфе с несколькими ботами не было ложных срабатываний\n\n" \
        "Настройки мемы (вкл/выкл) - определяет, будет ли бот присылать мем если прислано его точное название без / (боту требуется доступ к переписке). " \
        "Для доверенных:\n" \
        "Настройки майнкрафт (вкл/выкл) - определяет, будет ли бот присылать информацию о серверах майна."

    def start(self):
        if self.event.args:
            arg0 = self.event.args[0].lower()
        else:
            arg0 = None

        menu = [
            [['реагировать', 'реагируй', 'реагирование'], self.menu_reaction],
            [['майнкрафт', 'майн', 'minecraft', 'mine'], self.menu_minecraft_notify],
            [['мемы'], self.menu_memes],
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
        self.check_sender(Role.CONFERENCE_ADMIN)
        self.check_args(2)
        value = self.get_on_or_off(self.event.args[1].lower())

        self.check_conversation()
        self.event.chat.need_reaction = value
        self.event.chat.save()
        return "Сохранил настройку"

    def menu_memes(self):
        self.check_sender(Role.CONFERENCE_ADMIN)
        self.check_args(2)

        value = self.get_on_or_off(self.event.args[1].lower())
        self.check_conversation()
        self.event.chat.need_meme = value
        self.event.chat.save()
        return "Сохранил настройку"

    def menu_minecraft_notify(self):
        self.check_sender(Role.TRUSTED)
        self.check_args(2)

        value = self.get_on_or_off(self.event.args[1].lower())

        group_minecraft_notify = Group.objects.get(name=Role.MINECRAFT_NOTIFY.name)
        if value:
            self.event.sender.groups.add(group_minecraft_notify)
            self.event.sender.save()
            return "Подписал на рассылку о сервере майна"
        else:
            self.event.sender.groups.remove(group_minecraft_notify)
            self.event.sender.save()
            return "Отписал от рассылки о сервере майна"

    def menu_default(self):
        msg = "Настройки:\n"
        if self.event.chat:
            reaction = self.event.chat.need_reaction
            need_meme = self.event.chat.need_meme
            msg += f"Реагировать на неправильные команды - {TRUE_FALSE_TRANSLATOR[reaction]}\n"
            msg += f"Присылать мемы по точным названиям - {TRUE_FALSE_TRANSLATOR[need_meme]}\n"

        if self.event.sender.check_role(Role.TRUSTED):
            minecraft_notify = self.event.sender.check_role(Role.MINECRAFT_NOTIFY)
            msg += f"Уведомления по майну - {TRUE_FALSE_TRANSLATOR[minecraft_notify]}\n"
        return msg
