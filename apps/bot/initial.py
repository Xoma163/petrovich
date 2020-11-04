import importlib
import os
import pkgutil

from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from petrovich.settings import BASE_DIR


def import_all_commands():
    base_commands_folder_dir = f"{BASE_DIR}/apps/bot/commands"
    commands_dirs = []
    for path in os.walk(base_commands_folder_dir):
        if not path[0].endswith('__pycache__'):
            commands_dirs.append(path[0])

    for (module_loader, name, _) in pkgutil.iter_modules(commands_dirs):
        package = module_loader.path.replace(BASE_DIR, '')[1:].replace('/', '.')
        importlib.import_module('.' + name, package)


def generate_commands():
    _commands = [cls() for cls in CommonCommand.__subclasses__()]

    for command in _commands:
        if not command.enabled:
            _commands.remove(command)
    _commands.sort(key=lambda x: x.priority, reverse=True)
    return _commands


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

    groups_with_games = GROUPS + ["games"]
    help_text_generated = {platform: {group: "" for group in groups_with_games} for platform in list(Platform)}
    help_text_list = {platform: {group: [] for group in groups_with_games} for platform in list(Platform)}
    # help_text_list = {group: [] for group in groups_with_games}
    # api_help_text_list = {group: [] for group in groups_with_games}
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
                        for platform in command.platforms:
                            append_to_list(help_text_list[platform])

    for platform in list(Platform):
        for group in groups_with_games:
            help_text_list[platform][group].sort()
            help_text_generated[platform][group] = "\n".join(help_text_list[platform][group])

    return help_text_generated


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

GROUPS = generate_groups()

KEYBOARDS = generate_keyboard()

HELP_TEXTS = generate_help_text()

EMPTY_KEYBOARD = {
    "one_time": False,
    "buttons": []
}
