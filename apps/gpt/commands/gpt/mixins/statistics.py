import datetime
import io

import matplotlib.pyplot as plt
from django.db.models import Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from matplotlib.dates import DateFormatter
from matplotlib.ticker import MaxNLocator

from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextArgument
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem
from apps.bot.models import Profile
from apps.gpt.api.responses import GPTAPIResponse
from apps.gpt.models import Usage
from apps.gpt.protocols import GPTCommandProtocol


class GPTStatisticsMixin(GPTCommandProtocol):
    STATISTICS_HELP_TEXT_ITEMS = [
        HelpTextArgument("стата", "статистика по использованию"),
    ]

    # MENU

    def menu_statistics(self) -> ResponseMessageItem:
        """
        Просмотр статистики по использованию
        """
        self.check_pm()
        text_answer = self._get_statistics_for_user(self.event.sender)
        if not text_answer:
            raise PWarning("Ещё не было использований GPT")

        plot_data = self._get_data_for_statistics_plot(self.event.sender)
        plot_bytes = self._get_statistics_plot(plot_data)

        statistics_plot_image = PhotoAttachment()
        statistics_plot_image.parse(plot_bytes)
        return ResponseMessageItem(text_answer, attachments=[statistics_plot_image])

    # HANDLERS

    def _get_statistics_for_user(self, profile: Profile) -> str | None:
        """
        Получение статистики
        """

        """
        Запрос для статистики за 3 месяца по юзерам без ключа

        [x for x in GPTUsage.objects.filter(created_at__gte=datetime.datetime.now() - datetime.timedelta(days=30)) \
            .values('author__name') \
            .filter(Q(author__settings__chat_gpt_key='') | Q(author__settings__chat_gpt_key__isnull=True))
            .annotate(total_cost=Round(Sum('cost'),2), total_requests=Count('id')) \
            .order_by('-total_cost')]
        """

        stats_all = self._get_stat_db_profile(Q(author=profile))
        if not stats_all:
            return None

        # Начало и конец предыдущего месяца
        dt_now = timezone.now()
        first_day_of_current_month = dt_now.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - datetime.timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)

        stats_today = self._get_stat_db_profile(
            Q(author=profile, created_at__gte=dt_now - datetime.timedelta(days=1))
        )
        stats_7_day = self._get_stat_db_profile(
            Q(author=profile, created_at__gte=dt_now - datetime.timedelta(days=7))
        )

        last_month = self._get_stat_db_profile(
            Q(author=profile, created_at__gte=first_day_of_last_month, created_at__lt=first_day_of_current_month)
        )

        current_month = self._get_stat_db_profile(
            Q(author=profile, created_at__gte=first_day_of_current_month, created_at__lt=dt_now)
        )

        text_answer = f"{profile}:\n" \
                      f"Сегодня - $ {round(stats_today, 2)}\n" \
                      f"7 дней - $ {round(stats_7_day, 2)}\n" \
                      f"Прошлый месяц- $ {round(last_month, 2)}\n" \
                      f"Текущий месяц- $ {round(current_month, 2)}\n" \
                      f"Всего - $ {round(stats_all, 2)}"

        return text_answer

    # COMMON UTILS

    def add_statistics(self, api_response: GPTAPIResponse):
        Usage(
            author=self.event.sender,
            cost=api_response.usage.total_cost,
            provider=self.provider,
            model_name=api_response.usage.model.name
        ).save()

    # UTILS

    @staticmethod
    def _get_data_for_statistics_plot(profile):
        one_month_ago = timezone.now() - datetime.timedelta(days=30)

        usage_stats = Usage.objects.filter(
            author=profile,
            created_at__gte=one_month_ago
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total_cost=Sum('cost')
        ).order_by('date')

        stats_dict = {entry['date']: round(entry['total_cost'], 2) for entry in usage_stats}
        all_dates = [one_month_ago.date() + datetime.timedelta(days=x) for x in range(31)]

        return {date: stats_dict.get(date, float(0)) for date in all_dates}

    def _get_statistics_plot(self, stats_dict) -> bytes:
        dates = list(stats_dict.keys())
        costs = list(stats_dict.values())

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
        plt.title(f'Использование {self.provider.name} за последние 30 дней', fontsize=16)
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
        q |= Q(provider=self.provider.name)
        res = Usage.objects.filter(q).aggregate(Sum('cost')).get('cost__sum')
        return res if res else 0
