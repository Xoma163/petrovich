import datetime

from django.core.management.base import BaseCommand

from apps.bot.classes.bots.VkBot import VkBot
from apps.timetable.models import Group, Lesson

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
        self.bot = VkBot()
        self.now = datetime.datetime.now()
        iso_calendar = self.now.isocalendar()
        self.now_week_number = str((self.now.isocalendar()[1]) % 2 + 1)
        self.now_weekday = str(iso_calendar[2])

        self.chat_id = None
        self.default_title = None
        self.schedule = None
        # self.now = datetime.datetime(2020, 9, 7, 18, 50, 1)

    def find_first_lesson_number(self):
        lessons = self.schedule.get(self.now_week_number).get(self.now_weekday)
        if lessons:
            try:
                return int(list(lessons)[0])
            except:
                return None
        else:
            return None

    def find_last_lesson_number(self):
        lessons = self.schedule.get(self.now_week_number).get(self.now_weekday)
        if lessons:
            try:
                return int(list(lessons)[-1])
            except:
                return None
        else:
            return None

    @staticmethod
    def get_lesson_number(dt):
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

        groups = Group.objects.all()
        for group in groups:
            self.chat_id = group.conference.chat_id
            self.default_title = group.number
            self.schedule = Lesson.objects.filter(group=group)

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

            lesson = self.schedule.get(self.now_week_number, {}).get(self.now_weekday, {}).get(display_lesson_number)
            if lesson:
                lesson['number'] = display_lesson_number
            else:
                lesson = None
            new_title = self.prepare_title_for_lesson(lesson)

            self.set_title(new_title)
