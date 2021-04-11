import datetime

from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.timetable.models import Group


class TimeTable(CommonCommand):
    name = "неделя"
    help_text = "присылает номер недели в зависимости от группы"
    platforms = Platform.VK
    conversation = True

    def start(self):
        group = Group.objects.filter(conference=self.event.chat).first()
        if not group:
            return "Этой группы нет в базе"
        now = datetime.datetime.now()
        first_pair_week_number = group.first_lesson_day.isocalendar()[1]
        now_week_number = now.isocalendar()[1] - first_pair_week_number + 1
        return f"{now_week_number} неделя"
