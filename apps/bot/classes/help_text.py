from typing import List, Optional

from apps.bot.classes.const.consts import Role


class HelpTextItem:
    def __init__(self, role: Role, texts: List[str]):
        self.role = role
        self.texts = texts


class HelpText:
    """
    Вспомогательный класс для помощи пользователям с командами

    commands_text: Текст который будет выводиться для команды /команды (список всех команд)
    help_texts: Текст, который будет выводиться для команды /помощь {название команды}. С учётом ролей пользователя
    extra_text: Текст который также будет выводиться для команды /помощь {название команды} отдельно внизу
    """

    def __init__(self, commands_text, extra_text=None, help_texts: List[HelpTextItem] = None):

        if help_texts is None:
            help_texts = []

        self.commands_text = commands_text
        self.extra_text = extra_text

        self.items = {}
        for hti in help_texts:
            hti: HelpTextItem
            self.items[hti.role] = hti

    def get_help_text_item(self, role: Role) -> Optional[str]:
        hti = self.items.get(role)
        return hti if hti else None
