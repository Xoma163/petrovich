import datetime
import json

from django.core.management.base import BaseCommand

from apps.bot.classes.bots.VkBot import VkBot
from petrovich.settings import BASE_DIR

timetable = {
    '1': {'start': '8:00', 'end': '9:35'},
    '2': {'start': '9:45', 'end': '11:20'},
    '3': {'start': '11:30', 'end': '13:05'},
    '4': {'start': '13:30', 'end': '15:05'},
    '5': {'start': '15:15', 'end': '16:50'},
    '6': {'start': '17:00', 'end': '18:35'},
    '7': {'start': '18:45', 'end': '20:15'},
    '8': {'start': '20:25', 'end': '21:55'},
}
BEFORE_MIN = 10


class Command(BaseCommand):

    def __init__(self):
        super().__init__()
        self.chat_id = 20
        self.default_title = '2508'

        with open(BASE_DIR + '/static/schedules/schedule.json') as json_file:
            self.schedule = json.load(json_file)

        self.bot = VkBot()

        self.now = datetime.datetime.now()
        # self.now = datetime.datetime(2020, 9, 7, 18, 50, 1)
        iso_calendar = self.now.isocalendar()
        self.now_weeknumber = str((self.now.isocalendar()[1]) % 2 + 1)
        self.now_weekday = str(iso_calendar[2])

    # def handle(self, *args, **kwargs):
    #      with open(BASE_DIR + '/static/schedules/schedule.json') as json_file:
    #          schedule = json.load(json_file)
    #      # now = datetime.datetime.now()
    #      now = datetime.datetime(2020, 9, 7, 11, 21, 0)
    #      now_week_number = str((now.isocalendar()[1]) % 2 + 1)
    #      now_weekday = str(now.weekday() + 1)
    #
    #      # Проверяем есть ли сегодня пары
    #      if now_week_number not in schedule:
    #          self.change_title_on_default()
    #          return
    #      if now_weekday not in schedule[now_week_number]:
    #          self.change_title_on_default()
    #          return
    #
    #      # Узнаём какая пара первая, а какая последняя
    #      for i in range(len(timetable)):
    #          if str(i + 1) in schedule[now_week_number][now_weekday]:
    #              if self.first_discipline is None:
    #                  self.first_discipline = str(i + 1)
    #              self.last_discipline = str(i + 1)
    #
    #      new_min = now.minute
    #      new_hour = now.hour
    #      if new_min >= 60:
    #          new_min -= 60
    #          new_hour += 1
    #      if new_hour >= 24:
    #          new_hour -= 24
    #
    #      now_1900 = datetime.datetime.strptime("%s:%s" % (new_hour, new_min), '%H:%M')
    #      current_discipline = None
    #      for item in timetable:
    #          item_date_start = datetime.datetime.strptime(timetable[item]['START'], '%H:%M')
    #          item_date_end = datetime.datetime.strptime(timetable[item]['END'], '%H:%M')
    #          if item_date_start <= now_1900 <= item_date_end or \
    #                  datetime.timedelta(0) < item_date_start - now_1900 <= datetime.timedelta(minutes=BEFORE_MIN):
    #              # if item_date_start <= now_1900 <= item_date_end:
    #              current_discipline = str(item)
    #      if now_1900 <= datetime.datetime.strptime(timetable['1']['START'], '%H:%M'):
    #          current_discipline = 0
    #      elif now_1900 >= datetime.datetime.strptime(timetable['6']['END'], '%H:%M'):
    #          current_discipline = 7
    #
    #      # Установка первой по расписанию пары
    #      if int(current_discipline) < int(self.first_discipline):
    #          vk_title = "2508|{} {} {}({})".format(
    #              timetable[self.first_discipline]['START'],
    #              schedule[now_week_number][now_weekday][self.first_discipline]['cabinet'],
    #              schedule[now_week_number][now_weekday][self.first_discipline]['teacher'],
    #              schedule[now_week_number][now_weekday][self.first_discipline]['type'],
    #          )
    #          bot.set_chat_title_if_not_equals(self.chat_id, vk_title)
    #          return
    #      # Текущая пара
    #      elif int(self.first_discipline) <= int(current_discipline) <= int(self.last_discipline):
    #          if current_discipline in schedule[now_week_number][now_weekday]:
    #              vk_title = "2508|{} {} {}({})".format(
    #                  timetable[current_discipline]['START'],
    #                  schedule[now_week_number][now_weekday][current_discipline]['cabinet'],
    #                  schedule[now_week_number][now_weekday][current_discipline]['teacher'],
    #                  schedule[now_week_number][now_weekday][current_discipline]['type'])
    #              bot.set_chat_title_if_not_equals(self.chat_id, vk_title)
    #              return
    #      # После пар
    #      elif int(current_discipline) > int(self.last_discipline):
    #          self.change_title_on_default()
    #      else:
    #          bot.set_chat_title_if_not_equals(self.chat_id, 'втф я сломался, АНДРЕЙ ЧИНИ')

    def find_first_lesson_number(self):
        lessons = self.schedule.get(self.now_weeknumber).get(self.now_weekday)
        if lessons:
            try:
                return int(list(lessons)[0])
            except:
                return None
        else:
            return None

    def find_last_lesson_number(self):
        lessons = self.schedule.get(self.now_weeknumber).get(self.now_weekday)
        if lessons:
            try:
                return int(list(lessons)[-1])
            except:
                return None
        else:
            return None

    def get_lesson_number(self, dt):
        dt = dt + datetime.timedelta(minutes=BEFORE_MIN)

        for i, lesson_number in enumerate(timetable):
            start = timetable[lesson_number]['start'].split(':')
            start_dt = dt.replace(hour=int(start[0]), minute=int(start[1]))
            end = timetable[lesson_number]['end'].split(':')
            end_dt = dt.replace(hour=int(end[0]), minute=int(end[1]))
            if start_dt <= dt <= end_dt:
                return int(lesson_number)
        return None

    def prepare_title_for_lesson(self, lesson):
        if lesson:
            return f"{self.default_title}|{timetable[lesson['number']]['start']} {lesson['cabinet']} {lesson['teacher']} ({lesson['type']})"
        else:
            return self.default_title

    def set_title(self, title):
        self.bot.set_chat_title_if_not_equals(self.chat_id, title)

    def handle(self, *args, **kwargs):
        lesson_number = self.get_lesson_number(self.now)
        first_lesson_number = self.find_first_lesson_number()
        last_lesson_number = self.find_last_lesson_number()

        display_lesson_number = None
        if not lesson_number and first_lesson_number:
            display_lesson_number = first_lesson_number
        else:
            if lesson_number < first_lesson_number:
                display_lesson_number = first_lesson_number
            elif first_lesson_number <= lesson_number <= last_lesson_number:
                display_lesson_number = lesson_number
            elif lesson_number > last_lesson_number:
                display_lesson_number = None
            else:
                print('wtf')

        display_lesson_number = str(display_lesson_number)

        lesson = self.schedule.get(self.now_weeknumber, {}).get(self.now_weekday, {}).get(display_lesson_number)
        if lesson:
            lesson['number'] = display_lesson_number
        else:
            lesson = None
        new_title = self.prepare_title_for_lesson(lesson)

        self.set_title(new_title)
