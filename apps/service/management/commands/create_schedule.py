import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from petrovich.settings import BASE_DIR


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # неделя, день недели, время
        # schedule[1][3][1]
        schedule2 = {}
        weeks = [1, 2]

        for week in weeks:
            response = requests.get('https://ssau.ru/rasp', params={'groupId': '530996320', 'selectedWeek': week})
            soup = BeautifulSoup(response.content, 'html.parser')
            timetable_html = soup.find('div', {'class': 'schedule__items'}).find_all('div', {'class': 'schedule__item'})

            timetable = timetable_html[7:]

            timetable_list = []
            row = []
            for i, item in enumerate(timetable):
                if (i + 1) % 6 == 0:
                    timetable_list.append(row)
                    row = []
                else:
                    row.append(item)
            timetable_list = list(zip(*timetable_list))
            for week_day, day in enumerate(timetable_list):
                for lesson_number, lesson in enumerate(day):
                    if lesson.find('div', {'class': 'schedule__lesson'}):

                        try:
                            teacher = lesson.find('div', {'class': 'schedule__teacher'}).text.strip()
                        except:
                            teacher = ""

                        try:
                            discipline = lesson.find('div', {'class': 'schedule__discipline'}).text.strip()
                        except:
                            discipline = ""

                        try:
                            cabinet = lesson.find('div', {'class': 'schedule__place'}).text.strip()
                        except:
                            cabinet = ""

                        if lesson.find('div', {'class': 'lesson-border-type-1'}):
                            _type = "🍏 Лекция"
                        elif lesson.find('div', {'class': 'lesson-border-type-2'}):
                            _type = "🍋 Лаба"
                        elif lesson.find('div', {'class': 'lesson-border-type-3'}):
                            _type = "🍎 Практика"
                        elif lesson.find('div', {'class': 'lesson-border-type-4'}):
                            _type = "Другое"
                        else:
                            _type = "втф"

                        real_week_day = week_day + 1
                        real_lesson_number = lesson_number + 1

                        if not schedule2.get(week, None):
                            schedule2[week] = {}
                        if not schedule2[week].get(real_week_day, None):
                            schedule2[week][real_week_day] = {}
                        if not schedule2[week][real_week_day].get(real_lesson_number, None):
                            schedule2[week][real_week_day][real_lesson_number] = {}
                        schedule2[week][real_week_day][real_lesson_number] = {
                            'teacher': teacher,
                            'discipline': discipline,
                            'cabinet': cabinet,
                            'type': _type
                        }
        path = BASE_DIR + '/static/schedules/'
        filename = 'schedule.json'
        Path(path).mkdir(parents=True, exist_ok=True)
        with open(path + filename, "w") as outfile:
            json.dump(schedule2, outfile)

        print('done')
