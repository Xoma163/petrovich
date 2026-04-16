from apps.bot.consts import RoleEnum, PlatformEnum
from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.commands.notifies.models import Notify
from apps.commands.notifies.services import NotifyCreateService, NotifyFormatter, NotifyQueryService
from apps.shared.exceptions import PWarning
from apps.shared.utils.utils import localize_datetime, remove_tz


class Notifies(Command):
    name = "напоминания"
    names = ["напоминание", "напомни", "напоминай"]

    help_text = HelpText(
        commands_text="установка напоминаний",
        help_texts=[
            HelpTextItem(
                RoleEnum.USER,
                [
                    HelpTextArgument(None, "список активных напоминаний в лс, если в конфе, то только общие в конфе"),
                    HelpTextArgument(
                        "добавить (дата/дата и время/день недели) (сообщение/команда) [вложения]",
                        "добавляет напоминание",
                    ),
                    HelpTextArgument(
                        "добавить (crontab) (сообщение/команда) [вложения]", "добавляет постоянное напоминание"
                    ),
                    HelpTextArgument("удалить (текст/дата/crontab/id)", "удаляет напоминание"),
                ],
            )
        ],
        extra_text="Максимум можно добавить 5 напоминаний\n\nПомощник для добавления crontab: https://crontab.guru/",
    )

    platforms = [PlatformEnum.TG]

    bot: TgBot

    def start(self) -> ResponseMessage:
        if not self.event.sender.city:
            error = "Не указан город в профиле. /профиль город (название) - устанавливает город пользователю.\nБез него я не смогу узнать часовой пояс"
            raise PWarning(error)

        arg0 = self.event.message.args[0] if self.event.message.args else None
        menu = [
            [["удалить", "удали"], self.menu_delete],
            [["добавить", "добавь"], self.menu_add],
            [["default"], self.menu_get_notifies],
        ]
        method = self.handle_menu(menu, arg0)
        rmi = method()
        return ResponseMessage(rmi)

    def menu_add(self) -> ResponseMessageItem:
        self.check_max_notifies()
        self.check_args(2)

        notify_data = NotifyCreateService(self.event, self.full_names).build_notify_data()
        notify = Notify(**notify_data.as_model_kwargs())
        notify.save()

        if notify.crontab:
            answer = "Добавил напоминание"
        else:
            timezone = self.event.sender.city.timezone.name
            localized_dt = localize_datetime(remove_tz(notify.date), timezone)
            answer = f"Сохранил на дату {localized_dt.strftime('%d.%m.%Y %H:%M')}"

        return ResponseMessageItem(text=answer)

    def menu_delete(self) -> ResponseMessageItem:
        self.check_args(2)

        channel_filter = self.event.message.args[1:]
        notifie = self.get_notifie(channel_filter)

        notifie.delete()
        answer = "Удалил"
        return ResponseMessageItem(text=answer)

    def menu_get_notifies(self) -> ResponseMessageItem:
        notifies = NotifyQueryService(self.event, self.bot).get_filtered_notifies()
        formatter = NotifyFormatter(self.bot, self.event.sender.city.timezone.name)
        return ResponseMessageItem(text=formatter.format_many(notifies))

    def get_notifie(self, filters: list) -> Notify:
        return NotifyQueryService(self.event, self.bot).get_notify(filters)

    def get_notifies_str(self, notifies_obj, timezone):
        formatter = NotifyFormatter(self.bot, timezone)
        return formatter.format_many(notifies_obj)

    def check_max_notifies(self):
        if not self.event.sender.check_role(RoleEnum.TRUSTED) and len(Notify.objects.filter(user=self.event.user)) >= 5:
            raise PWarning("Нельзя добавлять более 5 напоминаний")
