import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from petrovich.settings import BASE_DIR


class Command(BaseCommand):
    # 5: {
    #     'teacher': "",
    #     'discipline': "",
    #     'cabinet': '',
    #     'type': ""
    # },

    def handle(self, *args, **kwargs):
        # неделя, день недели, время
        # schedule[1][3][1]
        schedule = {
            1: {
                2: {
                    1: {
                        'teacher': "Трафимова Г.А.",
                        'discipline': "САИД",
                        'cabinet': 'ON-LINE 5',
                        'type': "🍎 Практика"
                    }
                },
                3: {
                    1: {
                        'teacher': "Товарищ Майор",
                        'discipline': "Военка",
                        'cabinet': 'Военка',
                        'type': "🍎 Практика"
                    },
                    2: {
                        'teacher': "Товарищ Майор",
                        'discipline': "Военка",
                        'cabinet': 'Военка',
                        'type': "🍎 Практика"
                    },
                    3: {
                        'teacher': "Товарищ Майор",
                        'discipline': "Военка",
                        'cabinet': 'Военка',
                        'type': "🍎 Практика"
                    },
                    4: {
                        'teacher': "Товарищ Майор",
                        'discipline': "Военка",
                        'cabinet': 'Военка',
                        'type': "🍎 Практика"
                    },
                    5: {
                        'teacher': "Товарищ Майор",
                        'discipline': "Военка",
                        'cabinet': 'Военка',
                        'type': "🍎 Практика"
                    },

                },
                4: {
                    5: {
                        'teacher': "Мещеряков А.В.",
                        'discipline': "БУИП",
                        'cabinet': '128-5',
                        'type': "🍏 Лекция"
                    },
                    "6": {
                        'teacher': "Мещеряков А.В.",
                        'discipline': "БУИП",
                        'cabinet': '128-5',
                        'type': "🍎 Практика"
                    }
                },
                5: {
                    1: {
                        'teacher': "Быстров Н.Д.",
                        'discipline': "АИР",
                        'cabinet': '326-14',
                        'type': "Другое"
                    },
                    2: {
                        'teacher': "Быстров Н.Д.",
                        'discipline': "АИР",
                        'cabinet': '337-14',
                        'type': "🍏 Лекция"
                    },
                    3: {
                        'teacher': "Курбатов В.П.",
                        'discipline': "ТПРД",
                        'cabinet': '128-5',
                        'type': "🍏 Лекция"
                    },
                    4: {
                        'teacher': "Курбатов В.П.",
                        'discipline': "ТПРД",
                        'cabinet': 'кафедра-5',
                        'type': "Другое"
                    },
                },
            },
            2: {
                1: {
                    3: {
                        'teacher': "Паровай Ф.В.",
                        'discipline': "НРД",
                        'cabinet': '205/210-14',
                        'type': "🍎 Практика"
                    },
                    4: {
                        'teacher': "Паровай Ф.В.",
                        'discipline': "НРД",
                        'cabinet': '205/210-14',
                        'type': "🍎 Практика"
                    },
                    5: {
                        'teacher': "Жижкин А.М.",
                        'discipline': "КиПРД",
                        'cabinet': '202/ангар-14',
                        'type': "🍏 Лекция"
                    },
                    6: {
                        'teacher': "Жижкин А.М.",
                        'discipline': "КиПРД",
                        'cabinet': '202-14',
                        'type': "🍎 Практика"
                    },
                },
                2: {
                    1: {
                        'teacher': "Курбатов В.П.",
                        'discipline': "ТПРД",
                        'cabinet': '136-5/128-5',
                        'type': "🍋 Лаба"
                    },
                    2: {
                        'teacher': "Курбатов В.П.",
                        'discipline': "ТПРД",
                        'cabinet': '136-5/128-5',
                        'type': "🍋 Лаба"
                    },
                    3: {
                        'teacher': "Быстров Н.Д",
                        'discipline': "АиР",
                        'cabinet': '323/332-14',
                        'type': "🍋 Лаба"
                    },
                    4: {
                        'teacher': "Быстров Н.Д",
                        'discipline': "АиР",
                        'cabinet': '323/332-14',
                        'type': "🍋 Лаба"
                    },

                },
                3: {
                    1: {
                        'teacher': "Товарищ Майор",
                        'discipline': "Военка",
                        'cabinet': 'Военка',
                        'type': "🍎 Практика"
                    },
                    2: {
                        'teacher': "Товарищ Майор",
                        'discipline': "Военка",
                        'cabinet': 'Военка',
                        'type': "🍎 Практика"
                    },
                    3: {
                        'teacher': "Товарищ Майор",
                        'discipline': "Военка",
                        'cabinet': 'Военка',
                        'type': "🍎 Практика"
                    },
                    4: {
                        'teacher': "Товарищ Майор",
                        'discipline': "Военка",
                        'cabinet': 'Военка',
                        'type': "🍎 Практика"
                    },
                    5: {
                        'teacher': "Товарищ Майор",
                        'discipline': "Военка",
                        'cabinet': 'Военка',
                        'type': "🍎 Практика"
                    },
                },
                4: {
                    3: {
                        'teacher': "Быстров Н.Д.",
                        'discipline': "АиР",
                        'cabinet': '326-14',
                        'type': "🍏 Лекция"
                    },
                    4: {
                        'teacher': "Жижкин А.М.",
                        'discipline': "КиПРД",
                        'cabinet': '108-14/202',
                        'type': "🍏 Лекция"
                    },
                    5: {
                        'teacher': "Жижкин А.М.",
                        'discipline': "КиПРД",
                        'cabinet': '108/202/ангар-14',
                        'type': "🍋 Лаба"
                    },
                    6: {
                        'teacher': "Жижкин А.М.",
                        'discipline': "КиПРД",
                        'cabinet': '108/202/ангар-14',
                        'type': "🍋 Лаба"
                    },
                },
                5: {
                    2: {
                        'teacher': "Егорычев В.С.",
                        'discipline': "ДУиЭКА",
                        'cabinet': '315/325-5',
                        'type': "🍏 Лекция"
                    },
                    3: {
                        'teacher': "Егорычев В.С.",
                        'discipline': "ДУиЭКА",
                        'cabinet': '315/325-5',
                        'type': "🍎 Практика"
                    },
                },
                6: {
                    1: {
                        'teacher': "Паровай Ф.В.",
                        'discipline': "НРД",
                        'cabinet': '203-14',
                        'type': "🍋 Лаба"
                    },
                    2: {
                        'teacher': "Паровай Ф.В.",
                        'discipline': "НРД",
                        'cabinet': '203-14',
                        'type': "🍋 Лаба"
                    },
                }
            }}
        schedule2 = {}
        weeks = [1, 2]

        for week in weeks:
            response = requests.get('https://ssau.ru/rasp', params={'groupId': '530996320', 'selectedWeek': 1})
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
