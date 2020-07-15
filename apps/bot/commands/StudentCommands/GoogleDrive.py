from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class GoogleDrive(CommonCommand):
    def __init__(self):
        names = ["гугл", "ссылка", "учебное"]
        help_text = "Учебное - ссылка на папку с учебным материалом"
        keyboard = {'for': Role.STUDENT, 'text': 'Учебное', 'color': 'blue', 'row': 1, 'col': 3}
        super().__init__(names, help_text, access=Role.STUDENT, keyboard=keyboard)

    def start(self):
        url = "https://drive.google.com/open?id=1AJPnT2XXYNc39-2CSr_MzHnv4hs6Use6"
        return {'msg': url, 'attachments': [url]}
