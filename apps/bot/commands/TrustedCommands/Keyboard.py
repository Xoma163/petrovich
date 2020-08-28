from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand


class Keyboard(CommonCommand):
    def __init__(self):
        names = ["клава", "клавиатура"]
        help_text = "Клава - показать клавиатуру"
        # ToDo: access trusted это временное решение. Нужно будет пересмотреть политику клавиатур
        super().__init__(names, help_text, platforms=['vk', 'tg'], access=Role.TRUSTED, enabled=False)

    def start(self):
        return {"keyboard": get_keyboard(self.event.sender)}


def get_keyboard(sender):
    from apps.bot.initial import KEYBOARDS

    buttons = []

    user_groups = sender.get_list_of_role_names()

    for group in user_groups:
        buttons += KEYBOARDS[group]

    keyboard = {
        "one_time": False,
        "buttons": buttons
    }
    return keyboard
