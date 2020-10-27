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
        # self.now = datetime.datetime(2020, 9, 18, 9, 40)

        iso_calendar = self.now.isocalendar()

        self.now_week_number = None
        self.now_weekday = str(iso_calendar[2])

        self.chat_id = None
        self.default_title = None
        self.schedule = None
        self.schedule_today = None

    def find_first_lesson_number(self):
        first_lesson = self.schedule_today.order_by('lesson_number').first()
        if first_lesson:
            return int(first_lesson.lesson_number)
        else:
            return None

    def find_last_lesson_number(self):
        last_lesson = self.schedule_today.order_by('-lesson_number').first()
        if last_lesson:
            return int(last_lesson.lesson_number)
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
            if i == 0 and dt < start_dt:
                return -1
            if start_dt <= dt <= end_dt:
                return int(lesson_number)
        return None

    def prepare_title_for_lesson(self, lesson):
        if lesson:
            return f"{self.default_title}|{lesson.get_formatted()}"
        else:
            return self.default_title

    def set_title(self, title):
        self.bot.set_chat_title_if_not_equals(self.chat_id, title)

    def send_bbb_link(self, link):
        self.bot.send_message(self.chat_id, f"Ссылка на пару в bbb:\n{link}", attachments=[link])

    def handle(self, *args, **kwargs):

        groups = Group.objects.all()
        for group in groups:
            first_pair_week_number = group.first_lesson_day.isocalendar()[1]
            self.now_week_number = str(self.now.isocalendar()[1] - first_pair_week_number + 1)

            self.chat_id = group.conference.chat_id
            self.default_title = group.title or group.number
            self.schedule = Lesson.objects.filter(group=group)
            self.schedule_today = self.schedule.filter(week_number__contains=[self.now_week_number],
                                                       day_of_week=self.now_weekday)

            lesson_number = self.get_lesson_number(self.now)
            first_lesson_number = self.find_first_lesson_number()
            last_lesson_number = self.find_last_lesson_number()

            if not lesson_number:
                display_lesson_number = None
            else:
                if first_lesson_number and lesson_number < first_lesson_number:
                    display_lesson_number = first_lesson_number
                elif first_lesson_number and last_lesson_number and first_lesson_number <= lesson_number <= last_lesson_number:
                    display_lesson_number = lesson_number
                elif last_lesson_number and lesson_number > last_lesson_number:
                    display_lesson_number = None
                else:
                    display_lesson_number = None

            display_lesson_number = str(display_lesson_number)

            lesson = self.schedule_today.filter(lesson_number=display_lesson_number).first()
            new_title = self.prepare_title_for_lesson(lesson)
            try:
                self.set_title(str(new_title))
                if lesson and lesson.discipline.bbb_link:
                    self.send_bbb_link(lesson.discipline.bbb_link)

            except Exception as e:
                print(e)
                pass
