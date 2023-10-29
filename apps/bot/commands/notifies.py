from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import localize_datetime, remove_tz
from apps.service.models import Notify


class Notifies(Command):
    name = "напоминания"
    name_tg = "notifies"
    help_text = "список напоминаний"
    help_texts = [
        "- список активных напоминаний в лс, если в конфе, то только общие в конфе",
        "удалить (текст напоминания) - удаляет напоминание"
    ]
    platforms = [Platform.TG]
    city = True

    bot: TgBot

    def start(self) -> ResponseMessage:
        arg0 = self.event.message.args[0] if self.event.message.args else None
        menu = [
            [["удалить", "удали"], self.menu_delete],
            [['default'], self.menu_get_notifies],
        ]
        method = self.handle_menu(menu, arg0)
        rmi = method()
        return ResponseMessage(rmi)

    def menu_get_notifies(self) -> ResponseMessageItem:
        notifies = self.get_filtered_notifies()
        rmi = ResponseMessageItem(text=self.get_notifies_str(notifies, self.event.sender.city.timezone.name))
        return rmi

    def menu_delete(self) -> ResponseMessageItem:
        self.check_args(2)
        notifies = self.get_filtered_notifies()

        filter_list = self.event.message.args[1:]
        for _filter in filter_list:
            notifies = notifies.filter(text_for_filter__icontains=_filter)

        if len(notifies) == 0:
            raise PWarning("Не нашёл напоминаний по такому тексту")
        if len(notifies) > 1:
            raise PWarning(f"Нашёл сразу несколько. Уточните:\n\n"
                           f"{self.get_notifies_str(notifies, self.event.sender.city.timezone.name)}")

        notifies.delete()
        answer = "Удалил"
        return ResponseMessageItem(text=answer)

    def get_notifies_str(self, notifies_obj, timezone):
        if len(notifies_obj) == 0:
            raise PWarning("Нет напоминаний")
        result = ""

        for notify in notifies_obj:
            if notify.date:
                notify_datetime = localize_datetime(remove_tz(notify.date), timezone)
            else:
                notify_datetime = notify.crontab

            result += f"{notify.user}\n"
            if notify.repeat:
                if notify.crontab:
                    result += f"{self.bot.get_formatted_text_line(notify_datetime)} - Постоянное"
                else:
                    result += f"{self.bot.get_formatted_text_line(notify_datetime.strftime('%H:%M'))} - Постоянное"
            else:
                result += f"{self.bot.get_formatted_text_line(notify_datetime.strftime('%d.%m.%Y %H:%M'))} - Постоянное"
            if notify.chat:
                result += f" (Конфа - {notify.chat.name})"
            result += f"\n{self.bot.get_formatted_text_line(notify.text)}\n\n"

        result_without_mentions = result.replace('@', '@_')
        return result_without_mentions

    def get_filtered_notifies(self) -> Notify.objects:
        if self.event.chat:
            notifies = Notify.objects.filter(chat=self.event.chat)
        else:
            notifies = Notify.objects.filter(user=self.event.user)
        if notifies.count() == 0:
            raise PWarning("Нет активных напоминаний")
        return notifies.order_by("date")
