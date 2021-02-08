import datetime

from apps.bot.classes.Consts import WEEK_TRANSLATOR, WEEK_TRANSLATOR_REVERT, Role, DELTA_WEEKDAY, Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.timetable.models import Group, Lesson


class TimeTable(CommonCommand):
    names = ["расписание", "расп"]
    help_text = "Расписание - присылает расписание в конфах с расписанием"
    detail_help_text = "Расписание [номер недели=текущая]- присылает расписание на текущую неделю\n" \
                       "Расписание (день недели) [номер недели=текущая] - присылает расписание на день. " \
                       "Если указать номер недели, то на конкретную неделю"
    platforms = Platform.VK
    conversation = True
    access = Role.STUDENT

    def start(self):
        group = Group.objects.filter(conference=self.event.chat).first()
        if not group:
            return "Этой группы нет в базе"
        # group = Group.objects.first()
        arg0 = None
        if self.event.args:
            arg0 = self.event.args[0].lower()
        if self.event.args and arg0 in WEEK_TRANSLATOR:
            week_day = WEEK_TRANSLATOR[self.event.args[0]]
            week_number = None
            if len(self.event.args) >= 2:
                self.int_args = [1]
                self.parse_int()
                week_number = self.event.args[1]
            return self.get_str_schedule_for_day(group, week_day, week_number)
        elif self.event.args and arg0 in DELTA_WEEKDAY:
            now = datetime.datetime.now()
            week_day = now.isocalendar()[2]
            week_day += DELTA_WEEKDAY[arg0]
            return self.get_str_schedule_for_day(group, week_day)
        else:
            if self.event.args:
                self.int_args = [0]
                self.parse_int()
                week_number = arg0
            else:
                now = datetime.datetime.now()
                first_pair_week_number = group.first_lesson_day.isocalendar()[1]
                week_number = now.isocalendar()[1] - first_pair_week_number + 1
            result = f"{week_number} неделя\n\n"
            for week_day in range(1, 8):
                schedule_day, _, _ = self.get_schedule_for_day(group, week_day, week_number)
                if schedule_day:
                    result += f"{WEEK_TRANSLATOR_REVERT[week_day].capitalize()}\n" \
                              f"{self.get_str_lessons(schedule_day)}\n\n"
            return result

    def get_str_schedule_for_day(self, group, week_day, week_number=None):
        lessons, week_number, week_day = self.get_schedule_for_day(group, week_day, week_number)
        lessons_str = f"{WEEK_TRANSLATOR_REVERT[week_day]}. {week_number} неделя\n\n"
        lessons_str += self.get_str_lessons(lessons)
        return lessons_str

    @staticmethod
    def get_str_lessons(lessons):
        lessons_str = ""
        if not lessons:
            lessons_str += "Нет пар в этот день"
            return lessons_str
        for lesson in lessons:
            lessons_str += f"{lesson.get_formatted()}\n"
        return lessons_str

    @staticmethod
    def get_schedule_for_day(group, week_day, week_number=None):
        now = datetime.datetime.now()
        now_week_day = now.isocalendar()[2]

        if not week_number:
            first_pair_week_number = group.first_lesson_day.isocalendar()[1]
            week_number = now.isocalendar()[1] - first_pair_week_number + 1

            if week_day > 7:
                week_day -= 7
                week_number += 1
            if week_day < now_week_day:
                week_number += 1

        lessons = Lesson.objects.filter(
            group=group,
            week_number__contains=[week_number],
            day_of_week=week_day
        ).order_by('lesson_number')

        return lessons, week_number, week_day
