import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from django.core.management import BaseCommand
from matplotlib import ticker

from apps.bot.utils.utils import localize_datetime, remove_tz
from apps.service.models import TaxiInfo


class Command(BaseCommand):

    def __init__(self):
        super().__init__()

    @staticmethod
    def print_time_delivery_by_time_graphic():
        fig, ax = plt.subplots(1)
        fig.autofmt_xdate()

        plt.xlabel('Время')
        plt.ylabel('Время, мин.')
        plt.title('Время поездки в зависимости от времени. Маршрут дом-работа')

        plt.legend()
        xfmt = mdates.DateFormatter('%H:%M')
        ax.xaxis.set_major_formatter(xfmt)

        plt.show()

    @staticmethod
    def get_avg_price_data(data):
        len_data = len(data)
        x_data = [localize_datetime(remove_tz(x.created), 'Europe/Samara').replace(day=1, month=1, year=1900)
                  + datetime.timedelta(hours=4)
                  for x in data[list(data.keys())[0]]]
        y_data = [0 for _ in range(len(x_data))]
        for key in data:
            for i, item in enumerate(data[key]):
                try:
                    y = item.data['options'][1]['price']
                    y_data[i] += y / len_data
                except Exception:
                    pass

        return x_data, y_data

    def print_price_by_time_graphic(self, weekdays, friday, weekends):
        weekdays_x, weekdays_y = self.get_avg_price_data(weekdays)
        friday_x, friday_y = self.get_avg_price_data(friday)
        weekends_x, weekends_y = self.get_avg_price_data(weekends)
        fig, ax = plt.subplots(1)
        fig.autofmt_xdate()

        xfmt = mdates.DateFormatter('%H:%M')
        ax.xaxis.set_major_formatter(xfmt)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(1 / 24))

        ax.grid(which='major',
                color='k')

        ax.grid(which='minor',
                color='gray',
                linestyle=':')

        window_len = 10  # minutes
        kernel = np.ones(window_len, dtype=float) / window_len
        friday_y = np.convolve(friday_y, kernel, 'same')
        weekends_y = np.convolve(weekends_y, kernel, 'same')
        weekdays_y = np.convolve(weekdays_y, kernel, 'same')

        plt.plot(friday_x, friday_y, label='Пт', color='#0000ff', linewidth=3)
        plt.plot(weekends_x, weekends_y, label='Сб, Вс', color='#ff0000', linewidth=3)
        plt.plot(weekdays_x, weekdays_y, label='Пн-Чт', color='#00ff00', linewidth=3)

        plt.xlabel('Время', fontsize=21)
        plt.ylabel('Цена, руб.', fontsize=21)
        plt.title('Цена эконом тарифа в зависимости от времени. Маршрут дом-работа', fontsize=21)
        plt.legend()

        fig.set_figwidth(19.20)
        fig.set_figheight(10.80)

        plt.show()

    @staticmethod
    def get_grouped_taxi_infos(taxi_infos):
        dates = list(dict.fromkeys((x[0] for x in taxi_infos.values_list('created__date'))))
        return {date: taxi_infos.filter(created__date=date) for date in dates}

    def handle(self, *args, **kwargs):
        date_now = datetime.datetime.now().date()
        taxi_infos = TaxiInfo.objects.all().exclude(created__date=date_now).order_by('pk')

        taxi_info_weekday = taxi_infos.filter(created__week_day__in=[2, 3, 4, 5])
        taxi_info_weekday = self.get_grouped_taxi_infos(taxi_info_weekday)
        taxi_info_friday = taxi_infos.filter(created__week_day__in=[6])
        taxi_info_friday = self.get_grouped_taxi_infos(taxi_info_friday)
        taxi_info_weekend = taxi_infos.filter(created__week_day__in=[1, 7])
        taxi_info_weekend = self.get_grouped_taxi_infos(taxi_info_weekend)

        self.print_price_by_time_graphic(taxi_info_weekday, taxi_info_friday, taxi_info_weekend)
