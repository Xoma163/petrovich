import importlib
import os
import pkgutil

from django.contrib.auth.models import Group

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from petrovich.settings import BASE_DIR


def import_all_commands():
    base_commands_folder_dir = os.path.join(BASE_DIR, "apps", "bot", "commands")
    commands_dirs = []
    for path in os.walk(base_commands_folder_dir):
        if not path[0].endswith('__pycache__'):
            commands_dirs.append(path[0])

    for (module_loader, name, _) in pkgutil.iter_modules(commands_dirs):
        package = module_loader.path.replace(BASE_DIR, '')[1:].replace('/', '.')
        importlib.import_module('.' + name, package)


def generate_commands():
    commands = Command.__subclasses__()
    new_commands = commands
    flag = True
    while flag:
        new_commands = [x for x in [cls.__subclasses__() for cls in new_commands] if x]
        if new_commands:
            _new_commands = []
            for cmd in new_commands:
                _new_commands += cmd
            commands += _new_commands
            new_commands = _new_commands
        else:
            flag = False
    commands = [cls() for cls in commands if cls.enabled]
    commands.sort(key=lambda x: x.priority, reverse=True)
    return commands


def generate_help_text():
    def append_to_list(_list):
        text_for = text['for'].name
        if text_for in _list:
            _list[text_for].append(text['text'])
        else:
            print(f"Warn: Ошибка в генерации help_text. Ключ {text_for} не найден")

    groups = [x['name'] for x in Group.objects.all().values('name')]
    help_text_generated = {platform: {group: "" for group in groups} for platform in list(Platform)}
    help_text_list = {platform: {group: [] for group in groups} for platform in list(Platform)}

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
        for group in groups:
            help_text_list[platform][group].sort()
            help_text_generated[platform][group] = "\n".join(help_text_list[platform][group])

    return help_text_generated


import_all_commands()

COMMANDS = generate_commands()

HELP_TEXTS = generate_help_text()


def get_text_for_documentation(commands):
    nl = '\n'
    left_quote_new = '\['
    right_quote_new = '\]'

    doc_commands = sorted(
        [x for x in commands if x.access == Role.USER and x.name and x.suggest_for_similar and x.help_text],
        key=lambda y: y.name)
    documentation = []
    for doc_command in doc_commands:
        command_text = f"**/{doc_command.name.capitalize()}** - {doc_command.help_text}\n"
        if doc_command.help_texts:
            command_text = command_text + "<br>\n" + "<br>\n".join(
                [
                    f"**/{doc_command.name.capitalize()}** "
                    f"{x.replace(nl, '<br>').replace('[', left_quote_new).replace(']', right_quote_new)}{nl}"
                    for x in doc_command.help_texts
                ]
            )
        documentation.append(command_text)
    return "\n".join(documentation)
