from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.classes.common.CommonMethods import localize_datetime, remove_tz
from apps.service.models import Notify


def get_notifies_from_object(notifies_obj, timezone, print_username=False):
    if len(notifies_obj) == 0:
        return "Нет напоминаний"
    result = ""

    for notify in notifies_obj:
        notify_datetime = localize_datetime(remove_tz(notify.date), timezone)

        if print_username:
            result += f"{notify.author}\n"
        if notify.repeat:
            result += f"{str(notify_datetime.strftime('%H:%M'))} - Постоянное"
        else:
            result += f"{str(notify_datetime.strftime('%d.%m.%Y %H:%M'))}"
        if notify.chat:
            result += f" (Конфа - {notify.chat.name})"
        result += f"\n{notify.text}\n\n"

    return result

# ToDo: TG
class Notifies(CommonCommand):
    def __init__(self):
        names = ["напоминания", "оповещения"]
        help_text = "Напоминания - список напоминаний"
        detail_help_text = "Напоминания - список напоминаний. Отправляет в лс все напоминания, когда-либо созданные, в группу - только напоминания внутри группы\n" \
                           "Напоминания удалить (текст напоминания) - удаляет напоминания\n" \
                           "Напоминания конфа - выводит все напоминания по конфе\n" \
                           "Напоминания (имя, фамилия, логин/id, никнейм) - напоминания пользователя по конфе\n" \
                           "Админ конфы может удалять напоминания остальных участников"
        super().__init__(names, help_text, detail_help_text, api=False, enabled=False)

    def start(self):
        if self.event.sender.city is None:
            return "Не знаю ваш город. /город"
        self.user_timezone = self.event.sender.city.timezone.name

        if not self.event.args:
            return self.menu_notifications()
        else:
            arg0 = self.event.args[0].lower()

            menu = [
                [["удалить", "удали"], self.menu_delete],
                [["конфа", "беседе", "конфы", "беседы"], self.menu_conference],
                [['default'], self.menu_get_for_user],
            ]
            method = self.handle_menu(menu, arg0)
            return method()

    def menu_delete(self):
        self.check_args(2)
        notifies = Notify.objects.filter(author=self.event.sender).order_by("date")
        if self.event.chat:
            try:
                self.check_sender(Role.CONFERENCE_ADMIN)
                notifies = Notify.objects.filter(chat=self.event.chat).order_by("date")
            except RuntimeError:
                notifies = notifies.filter(chat=self.event.chat)
        filter_list = self.event.args[1:]
        for _filter in filter_list:
            notifies = notifies.filter(text_for_filter__icontains=_filter)

        if len(notifies) == 0:
            return "Не нашёл напоминаний по такому тексту"
        if len(notifies) > 1:
            notifies10 = notifies[:10]
            notifies_texts = [str(notify.author) + " " + notify.text_for_filter for notify in notifies10]
            notifies_texts_str = "\n".join(notifies_texts)
            return f"Нашёл сразу несколько. Уточните:\n" \
                   f"{notifies_texts_str}"

        notifies.delete()
        return "Удалил"

    def menu_conference(self):
        self.check_conversation()
        notifies = Notify.objects.filter(chat=self.event.chat)
        return get_notifies_from_object(notifies, self.user_timezone, True)

    def menu_get_for_user(self):
        self.check_conversation()
        user = self.bot.get_user_by_name(self.event.original_args, self.event.chat)
        notifies = Notify.objects.filter(author=user, chat=self.event.chat)
        return get_notifies_from_object(notifies, self.user_timezone, True)

    def menu_notifications(self):
        notifies = Notify.objects.filter(author=self.event.sender).order_by("date")
        if self.event.chat:
            notifies = notifies.filter(chat=self.event.chat)
        return get_notifies_from_object(notifies, self.user_timezone)
