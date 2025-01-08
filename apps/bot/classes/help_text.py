from apps.bot.classes.const.consts import Role


class HelpTextArgument:
    def __init__(self, args: str | None, description: str):
        self.args: str = args
        self.description: str = description


class HelpTextKey:
    def __init__(self, key: str, aliases: list[str] | None, description: str):
        self.key: str = key
        self.aliases: list[str] | None = aliases
        self.description: str = description

    def get_aliases(self) -> list[str]:
        return self.aliases if self.aliases else []

class HelpTextItem:
    def __init__(self, role: Role, texts: list[HelpTextArgument | HelpTextKey]):
        self.role: role = role
        self.items: list[HelpTextArgument] = texts


class HelpText:
    """
    Вспомогательный класс для помощи пользователям с командами

    commands_text: Текст который будет выводиться для команды /команды (список всех команд)
    help_texts: Текст, который будет выводиться для команды /помощь {название команды}. С учётом ролей пользователя
    extra_text: Текст который также будет выводиться для команды /помощь {название команды} отдельно внизу
    """

    def __init__(
            self,
            commands_text: str,
            extra_text: str = None,
            help_texts: list[HelpTextItem] = None,
            help_text_keys: list[HelpTextItem] = None,
    ):

        if help_texts is None:
            help_texts = []
        if help_text_keys is None:
            help_text_keys = []

        self.commands_text: str = commands_text
        self.extra_text: str = extra_text

        self.help_texts: dict[Role, HelpTextItem] = {}
        for hti in help_texts:
            hti: HelpTextItem
            self.help_texts[hti.role] = hti

        self.keys_items: dict[Role, HelpTextItem] = {}
        for htk in help_text_keys:
            htk: HelpTextItem
            self.keys_items[htk.role] = htk

    def get_help_text_item(self, role: Role) -> str | None:
        hti = self.help_texts.get(role)
        return hti if hti else None

    def get_help_text_key(self, role: Role) -> str | None:
        hti = self.keys_items.get(role)
        return hti if hti else None
