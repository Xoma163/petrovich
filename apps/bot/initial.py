import importlib
import os
import pkgutil

from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import BASE_DIR


def import_all_commands():
    BASE_COMMANDS_FOLDER_DIR = f"{BASE_DIR}/apps/bot/commands"
    COMMANDS_DIRS = []
    for path in os.walk(BASE_COMMANDS_FOLDER_DIR):
        if not path[0].endswith('__pycache__'):
            COMMANDS_DIRS.append(path[0])

    for (module_loader, name, _) in pkgutil.iter_modules(COMMANDS_DIRS):
        package = module_loader.path.replace(BASE_DIR, '')[1:].replace('/', '.')
        importlib.import_module('.' + name, package)


def generate_commands():
    _commands = [cls() for cls in CommonCommand.__subclasses__()]

    for command in _commands:
        if not command.enabled:
            _commands.remove(command)
    _commands.sort(key=lambda x: x.priority, reverse=True)
    return _commands


def get_commands():
    return COMMANDS


def generate_groups():
    from django.contrib.auth.models import Group

    groups = Group.objects.all().values('name')
    groups_names = [group['name'] for group in groups]
    return groups_names


def generate_help_text():
    def append_to_list(_list):
        # Если команда игра, то в отдельный список
        if command.__class__.__module__.split('.')[-2] == 'Games':
            _list['games'].append(text['text'])
        else:
            text_for = text['for'].name
            if text_for in _list:
                _list[text_for].append(text['text'])
            else:
                print(f"Warn: Ошибка в генерации help_text. Ключ {text_for} не найден")

    GROUPS_WITH_GAMES = GROUPS + ["games"]
    help_text_generated = {group: "" for group in GROUPS_WITH_GAMES}
    api_help_text_generated = {group: "" for group in GROUPS_WITH_GAMES}

    help_text_list = {group: [] for group in GROUPS_WITH_GAMES}
    api_help_text_list = {group: [] for group in GROUPS_WITH_GAMES}
    for command in COMMANDS:
        if command.help_text:
            help_text = command.help_text
            if isinstance(help_text, str):
                help_text = {'for': command.access, 'text': help_text}

            if isinstance(help_text, dict):
                help_text = [help_text]

            if isinstance(help_text, list):
                for text in help_text:
                    if command.enabled:
                        append_to_list(help_text_list)
                        if command.api is None or command.api:
                            append_to_list(api_help_text_list)

    for group in GROUPS_WITH_GAMES:
        help_text_list[group].sort()
        help_text_generated[group] = "\n".join(help_text_list[group])

        api_help_text_list[group].sort()
        api_help_text_generated[group] = "\n".join(api_help_text_list[group])
    return help_text_generated, api_help_text_generated


def generate_keyboard():
    keys = {group: [] for group in GROUPS}
    for command in COMMANDS:
        key = command.keyboard
        if key:
            if isinstance(key, dict):
                key = [key]
            if isinstance(key, list):
                for elem in key:
                    if 'for' in elem:
                        keys[elem['for'].name].append(elem)
                    else:
                        command_access = command.access.name
                        if command_access in keys:
                            keys[command_access].append(elem)
                        else:
                            print(
                                f"Warn: Ошибка в генерации клавиатуры. Ключ {command_access} для команды {command.names[0]} не найден")

    buttons = {group: [] for group in GROUPS}
    for k in keys:
        keys[k] = sorted(keys[k], key=lambda i: (i['row'], i['col']))
    color_translate = {
        'red': 'negative',
        'green': 'positive',
        'blue': 'primary',
        'gray': 'secondary'
    }

    for k in keys:
        row = []
        current_row = 0
        for key in keys[k]:
            if not current_row:
                row = []
                current_row = key['row']

            elif key['row'] != current_row:
                buttons[k].append(row)
                current_row = key['row']
                row = []

            row.append(
                {
                    "action": {
                        "type": "text",
                        "label": key['text']
                    },
                    "color": color_translate[key['color']]
                }
            )
        if len(row) > 0:
            buttons[k].append(row)
    return buttons


import_all_commands()

COMMANDS = generate_commands()

# underscore_symbol = "̲"
# for command in COMMANDS:
#     if command.help_text:
#         find_dash = command.help_text.find('-') - 1
#         underscore_help_text = underscore_symbol.join(list(command.help_text[:find_dash]))
#         other_help_text = command.help_text[find_dash:]
#         command.help_text = underscore_symbol + underscore_help_text + other_help_text

GROUPS = generate_groups()

KEYBOARDS = generate_keyboard()

HELP_TEXT, API_HELP_TEXT = generate_help_text()

EMPTY_KEYBOARD = {
    "one_time": False,
    "buttons": []
}
