import importlib
import os
import pkgutil

from apps.bot.classes.Consts import Platform, Role
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

    for command in COMMANDS:
        if command.help_text:
            help_text = command.help_text
            if isinstance(help_text, str):
                help_text = {'for': command.access, 'text': f"{command.name.capitalize()} - {help_text}"}
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

import_all_commands()

COMMANDS = generate_commands()

GROUPS = generate_groups()

HELP_TEXTS = generate_help_text()

EMPTY_KEYBOARD = {
    "one_time": False,
    "buttons": []
}

# doc_commands = sorted([x for x in COMMANDS if x.access == Role.USER and x.names[0] and x.suggest_for_similar], key=lambda y: y.names[0])