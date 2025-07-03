import datetime
import io
from zoneinfo import ZoneInfo

import matplotlib.pyplot as plt
from django.db.models import Q, Sum, QuerySet
from django.db.models.functions import TruncDate
from django.utils import timezone
from matplotlib.dates import DateFormatter
from matplotlib.ticker import MaxNLocator

from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument, HelpTextKey
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.bot.models import Profile
from apps.bot.utils.utils import decl_of_num
from apps.gpt.api.responses import GPTAPIResponse
from apps.gpt.models import Usage, ProfileGPTSettings
from apps.gpt.protocols import GPTCommandProtocol


class GPTStatisticsMixin(GPTCommandProtocol):
    STATISTICS_HELP_TEXT_ITEMS = [
        HelpTextArgument(
            "стата [дата 1] [дата 2]",
            "статистика по использованию. Если переданы аргументы, то пришлёт статистику за указаный период"
        ),
    ]
    STATISTICS_KEY_ITEMS_KEY = [
        HelpTextKey(
            "ключ",
            ['key'],
            "статистика пришлёт информацию по всем пользователям с этим ключом"
        ),
    ]

    # MENU

    def menu_statistics(self) -> ResponseMessageItem:
        """
        Просмотр статистики по использованию
        """
        self.check_pm()
        custom_range = self._get_custom_range_from_args()

        if self.event.message.is_key_provided({"ключ", "key"}):
            profiles = self._get_profiles_by_key()
            answer = self._get_statistics_per_profile(profiles, custom_range=custom_range)
        elif self.event.message.is_key_provided({"nokey"}):
            self.check_sender(Role.ADMIN)
            profiles = self._get_profiles_with_no_key()
            answer = self._get_statistics_per_profile(profiles, custom_range=custom_range)
        elif self.event.message.is_key_provided({"all"}):
            self.check_sender(Role.ADMIN)
            profiles = self._get_all_profiles()
            answer = self._get_statistics_per_profile(profiles, custom_range=custom_range)
        else:
            profiles = [self.event.sender]
            answer, _ = self._get_statistics_for_users(
                profiles,
                return_custom_data=bool(custom_range),
                custom_range=custom_range
            )

        if not answer:
            raise PWarning("Ещё не было использований GPT")

        plot_data = self._get_data_for_statistics_plot(profiles, custom_range=custom_range)
        plot_bytes = self._get_statistics_plot(plot_data)

        statistics_plot_image = PhotoAttachment()
        statistics_plot_image.parse(plot_bytes)
        return ResponseMessageItem(answer, attachments=[statistics_plot_image])

    # HANDLERS
    def _get_statistics_for_users(
            self,
            profiles: list[Profile],
            return_today_data: bool = True,
            return_7_day_data: bool = True,
            return_last_month_data: bool = True,
            return_current_month_data: bool = True,
            return_total_data: bool = True,
            return_custom_data: bool = False,
            custom_range: tuple = None
    ) -> tuple[str | None, float | None]:
        """Получение статистики по пользователям за разные периоды."""
        total_stats = self._get_stat_db_profile(Q(author__in=profiles))
        if not total_stats:
            return None, None

        now = timezone.now()
        current_month_start = now.replace(day=1)
        last_month_end = current_month_start - datetime.timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)

        profiles_str = ", ".join(map(str, profiles))
        answer = [f"{profiles_str}:"]

        periods = [
            (return_today_data, "Сегодня", now - datetime.timedelta(days=1), now),
            (return_7_day_data, "7 дней", now - datetime.timedelta(days=7), now),
            (return_last_month_data, "Прошлый месяц", last_month_start, current_month_start),
            (return_current_month_data, "Текущий месяц", current_month_start, now),
        ]

        for should_return, label, start, end in periods:
            if not should_return:
                continue
            stats = self._get_stat_db_profile(
                Q(author__in=profiles, created_at__gte=start, created_at__lt=end)
            )
            answer.append(f"{label} - $ {round(stats, 2)}")

        if return_custom_data:
            start, end = custom_range
            stats = self._get_stat_db_profile(
                Q(author__in=profiles, created_at__gte=start, created_at__lt=end)
            )
            answer.append(
                f"За период с {start.strftime('%d.%m.%Y')} по {end.strftime('%d.%m.%Y')} - $ {round(stats, 2)}")

        total_stats = round(total_stats, 2)
        if return_total_data:
            answer.append(f"Всего - $ {total_stats}")

        return "\n".join(answer), total_stats

    # COMMON UTILS

    def add_statistics(self, api_response: GPTAPIResponse):
        Usage(
            author=self.event.sender,
            cost=api_response.usage.total_cost,
            provider=self.provider_model,
            model_name=api_response.usage.model.name
        ).save()

    # UTILS

    def _get_profiles_by_key(self) -> QuerySet[Profile]:
        profile_key = self.get_profile_gpt_settings().get_key()
        if not profile_key:
            raise PWarning("У вас не установлен ключ")

        profiles_gpt_settings = ProfileGPTSettings.objects \
            .filter(provider=self.provider_model) \
            .exclude(key="")
        profiles_with_same_key = [
            x for x in profiles_gpt_settings
            if x.get_key() == profile_key
        ]
        profiles = Profile.objects.filter(gpt_settings__in=profiles_with_same_key)
        if profiles.count() == 1:
            raise PWarning("Не найдено других пользователей с вашим ключом")
        return profiles

    def _get_profiles_with_no_key(self) -> QuerySet[Profile]:
        profiles_gpt_settings = ProfileGPTSettings.objects \
            .filter(provider=self.provider_model) \
            .filter(key="")
        profiles = Profile.objects.filter(gpt_settings__in=profiles_gpt_settings)
        if profiles.count() == 0:
            raise PWarning("Не найдено пользователей без ключа")
        return profiles

    def _get_all_profiles(self) -> QuerySet[Profile]:
        profiles_gpt_settings = ProfileGPTSettings.objects \
            .filter(provider=self.provider_model)
        profiles = Profile.objects.filter(gpt_settings__in=profiles_gpt_settings)
        if profiles.count() == 0:
            raise PWarning("Не найдено пользователей")
        return profiles

    def _get_statistics_per_profile(
            self,
            profiles: QuerySet[Profile],
            custom_range: tuple[datetime, ...] | None = None
    ) -> str | None:
        stats_with_cost = []
        for profile in profiles:
            profile_stats, total_cost = self._get_statistics_for_users(
                [profile],
                return_today_data=False,
                return_7_day_data=False,
                return_custom_data=bool(custom_range),
                custom_range=custom_range
            )
            if profile_stats:
                stats_with_cost.append((profile_stats, total_cost))

        if not stats_with_cost:
            return None
        stats_with_cost.sort(key=lambda x: x[1], reverse=True)
        answers = [stats[0] for stats in stats_with_cost]

        if profiles.count() > 1:
            total_statistics, _ = self._get_statistics_for_users(
                list(profiles),
                return_today_data=False,
                return_7_day_data=False,
                return_custom_data=bool(custom_range),
                custom_range=custom_range
            )
            total_statistics = total_statistics.split('\n')
            total_statistics[0] = "Сумма по всем:"
            total_statistics = "\n".join(total_statistics)

            answers.append("-" * 10)
            answers.append(total_statistics)
        return "\n\n".join(answers)

    def _get_custom_range_from_args(self) -> tuple[datetime.datetime, ...] | None:
        if len(self.event.message.args) <= 1:
            return None

        start = self.event.message.args[1]
        end = None
        if len(self.event.message.args) > 2:
            end = self.event.message.args[2]

        tz = ZoneInfo('UTC')
        try:
            start_datetime = datetime.datetime.strptime(start, '%d.%m.%Y')
            start_datetime = start_datetime.replace(tzinfo=tz)

            if end:
                end_datetime = datetime.datetime.strptime(end, '%d.%m.%Y')
                end_datetime = end_datetime.replace(tzinfo=tz)

            else:
                end_datetime = timezone.now()
        except ValueError:
            raise PWarning("Ошибка в парсинге даты. Формат даты - ДД.ММ.ГГГГ")

        if start_datetime > end_datetime:
            start_datetime, end_datetime = end_datetime, start_datetime

        return start_datetime, end_datetime

    @staticmethod
    def _get_data_for_statistics_plot(profiles: list[Profile], custom_range: tuple[datetime, ...] | None = None):
        if not custom_range:
            start = timezone.now() - datetime.timedelta(days=30)
            end = timezone.now()
        else:
            start, end = custom_range
        days_count = (end - start).days + 1

        usage_stats = Usage.objects.filter(
            author__in=profiles,
            created_at__gte=start,
            created_at__lt=end
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total_cost=Sum('cost')
        ).order_by('date')

        stats_dict = {entry['date']: round(entry['total_cost'], 2) for entry in usage_stats}
        all_dates = [start.date() + datetime.timedelta(days=x) for x in range(days_count)]

        return {date: stats_dict.get(date, float(0)) for date in all_dates}

    def _get_statistics_plot(self, stats_dict) -> bytes:
        dates = list(stats_dict.keys())
        costs = list(stats_dict.values())

        days_count = len(dates)
        days_decl = decl_of_num(days_count, ["день", "дня", "дней"])

        # Преобразование дат в формат datetime для matplotlib
        dates = [datetime.datetime.combine(date, datetime.time()) for date in dates]

        # Создание фигуры и осей
        _, ax = plt.subplots(figsize=(12, 6))

        # Построение графика
        ax.plot(dates, costs, marker='o')

        # Настройка оси X для отображения дат
        ax.xaxis.set_major_formatter(DateFormatter('%d.%m'))
        ax.xaxis.set_major_locator(MaxNLocator(13))

        # Поворот меток на оси X для лучшей читаемости
        plt.xticks(rotation=45)

        # Настройка заголовка и подписей осей
        plt.title(f'Использование {self.provider.type_enum} за {days_count} {days_decl}', fontsize=16)
        plt.xlabel('Дата', fontsize=14)
        plt.ylabel('Стоимость, $', fontsize=14)

        # Добавление сетки для улучшения читаемости
        plt.grid(True, linestyle='--', alpha=0.7)

        # Улучшение расположения меток на оси X
        plt.tight_layout()

        # Сохранение графика в байтовый массив
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        return buf.getvalue()

    def _get_stat_db_profile(self, q):
        """
        Получение статистики в БД
        """
        q &= Q(provider=self.provider_model)
        res = Usage.objects.filter(q).aggregate(Sum('cost')).get('cost__sum')
        return res if res else 0
