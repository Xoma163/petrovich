from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.utils.utils import localize_datetime, remove_tz
from apps.service.models import Notify


def get_notifies_from_object(notifies_obj, timezone, print_username=False):
    if len(notifies_obj) == 0:
        raise PWarning("Нет напоминаний")
    result = ""

    for notify in notifies_obj:
        if notify.date:
            notify_datetime = localize_datetime(remove_tz(notify.date), timezone)
        else:
            notify_datetime = notify.crontab

        if print_username:
            result += f"{notify.user}\n"
        if notify.repeat:
            if notify.crontab:
                result += f"{notify_datetime} - Постоянное"
            else:
                result += f"{str(notify_datetime.strftime('%H:%M'))} - Постоянное"
        else:
            result += f"{str(notify_datetime.strftime('%d.%m.%Y %H:%M'))} - Постоянное"
        if notify.chat:
            result += f" (Конфа - {notify.chat.name})"
        result += f"\n{notify.text}\n\n"

    result_without_mentions = result.replace('@', '@_')
    return result_without_mentions


class Notifies(Command):
    name = "напоминания"
    name_tg = "notifies"
    help_text = "список напоминаний"
    help_texts = [
        "- список напоминаний. Отправляет в лс все напоминания, когда-либо созданные, в группу - только напоминания внутри группы",
        "удалить (текст напоминания) - удаляет напоминания. (Админ конфы может удалять любые напоминания в конфе)",
        "конфа - выводит все напоминания по конфе",
        "(имя, фамилия, логин/id, никнейм) - напоминания пользователя по конфе",
    ]
    platforms = [Platform.TG]
    city = True

    bot: TgBot

    def start(self):

        if not self.event.message.args:
            return self.menu_notifications()
        else:
            arg0 = self.event.message.args[0]
            menu = [
                [["удалить", "удали"], self.menu_delete],
                [["конфа", "беседе", "конфы", "беседы"], self.menu_conference],
                [['default'], self.menu_get_for_user],
            ]
            method = self.handle_menu(menu, arg0)
            return method()

    def menu_delete(self):
        self.check_args(2)
        notifies = Notify.objects.filter(user=self.event.user).order_by("date")
        if self.event.chat:
            try:
                self.check_sender(Role.CONFERENCE_ADMIN)
                notifies = Notify.objects.filter(chat=self.event.chat).order_by("date")
            except PWarning:
                notifies = notifies.filter(chat=self.event.chat)
        filter_list = self.event.message.args[1:]
        for _filter in filter_list:
            notifies = notifies.filter(text_for_filter__icontains=_filter)

        if len(notifies) == 0:
            raise PWarning("Не нашёл напоминаний по такому тексту")
        if len(notifies) > 1:
            notifies10 = notifies[:10]
            notifies_texts = [str(notify.user) + " " + notify.text_for_filter for notify in notifies10]
            notifies_texts_str = "\n".join(notifies_texts)
            raise PWarning(f"Нашёл сразу несколько. Уточните:\n"
                           f"{notifies_texts_str}")

        notifies.delete()
        return "Удалил"

    def menu_conference(self):
        self.check_conversation()
        notifies = Notify.objects.filter(chat=self.event.chat)
        return get_notifies_from_object(notifies, self.event.sender.city.timezone.name, True)

    def menu_get_for_user(self):
        self.check_conversation()
        profile = self.bot.get_profile_by_name(self.event.message.args_str, self.event.chat)
        user = profile.get_tg_user()
        notifies = Notify.objects.filter(user=user, chat=self.event.chat)
        return get_notifies_from_object(notifies, self.event.sender.city.timezone.name, True)

    def menu_notifications(self):
        notifies = Notify.objects.filter(user=self.event.user).order_by("date")
        if self.event.chat:
            notifies = notifies.filter(chat=self.event.chat)
        return get_notifies_from_object(notifies, self.event.sender.city.timezone.name)
