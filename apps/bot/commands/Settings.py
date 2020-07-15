from django.contrib.auth.models import Group

# ToDo: menu
from apps.bot.classes.Consts import ON_OFF_TRANSLATOR, Role, TRUE_FALSE_TRANSLATOR
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import check_user_group


class Settings(CommonCommand):
    def __init__(self):
        names = ["настройки", "настройка"]
        help_text = "Настройки - устанавливает некоторые настройки пользователя/чата"
        detail_help_text = "Настройки (настройка) (вкл/выкл) - устанавливает некоторые настройки пользователя/чата\n" \
                           "Настройки реагировать (вкл/выкл) - определяет, будет ли бот реагировать на неправильные команды в конфе. " \
                           "Это сделано для того, чтобы в конфе с несколькими ботами не было ложных срабатываний\n\n" \
                           "Для доверенных:\n" \
                           "Настройки майнкрафт (вкл/выкл) - определяет, будет ли бот присылать информацию о серверах майна."
        super().__init__(names, help_text, detail_help_text)

    def start(self):
        if self.event.args:
            self.check_args(2)
            if self.event.args[1].lower() in ON_OFF_TRANSLATOR:
                value = ON_OFF_TRANSLATOR[self.event.args[1]]
            else:
                return "Не понял, включить или выключить?"
            arg0 = self.event.args[0].lower()
            if arg0 in ['реагировать', 'реагируй', 'реагирование']:
                self.check_conversation()
                self.check_sender(Role.CONFERENCE_ADMIN)
                self.event.chat.need_reaction = value
                self.event.chat.save()
                return "Сохранил настройку"
            if arg0 in ['майнкрафт', 'майн', 'minecraft', 'mine']:
                self.check_sender(Role.TRUSTED)

                group_minecraft_notify = Group.objects.get(name=Role.MINECRAFT_NOTIFY.name)
                if value:
                    self.event.sender.groups.add(group_minecraft_notify)
                    self.event.sender.save()
                    return "Подписал на рассылку о сервере майна"
                else:
                    self.event.sender.groups.remove(group_minecraft_notify)
                    self.event.sender.save()
                    return "Отписал от рассылки о сервере майна"
            else:
                return "Не знаю такой настройки"
        else:
            msg = "Настройки:\n"
            if self.event.chat:
                reaction = self.event.chat.need_reaction
                msg += f"Реагировать на неправильные команды - {TRUE_FALSE_TRANSLATOR[reaction]}\n"

            if check_user_group(self.event.sender, Role.TRUSTED):
                minecraft_notify = check_user_group(self.event.sender, Role.MINECRAFT_NOTIFY)
                msg += f"Уведомления по майну - {TRUE_FALSE_TRANSLATOR[minecraft_notify]}\n"
            return msg
