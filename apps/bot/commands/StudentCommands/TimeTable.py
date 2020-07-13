import datetime

from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class TimeTable(CommonCommand):
    def __init__(self):
        names = ["расписание", "расп"]
        help_text = "Расписание - картинка с расписанием"
        keyboard_student = {'text': 'Расписание', 'color': 'blue', 'row': 1, 'col': 1}
        super().__init__(names, help_text, access=Role.STUDENT, keyboard=keyboard_student, enabled=False, platforms=['vk','tg'])

    def start(self):
        attachments = []
        photo = {'owner_id': f"-{self.bot.group_id}", 'id': 457239626}
        attachments.append(f"photo{photo['owner_id']}_{photo['id']}")
        return {'msg': str((datetime.datetime.now().isocalendar()[1] - 35)) + " неделя", 'attachments': attachments}
