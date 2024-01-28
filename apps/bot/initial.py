import importlib
import os
import pkgutil

from django.contrib.auth.models import Group

from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.utils.utils import get_flat_list
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
    groups = [x['name'] for x in Group.objects.all().values('name')]
    help_text_generated = {platform: {group: "" for group in groups} for platform in list(Platform)}
    help_text_list = {platform: {group: [] for group in groups} for platform in list(Platform)}

    for command in COMMANDS:
        if command.help_text and command.enabled:
            text = f"{command.name.capitalize()} - {command.help_text.commands_text}"
            for platform in command.platforms:
                text_for = command.access.name
                help_text_list[platform][text_for].append(text)

    for platform in list(Platform):
        for group in groups:
            help_text_list[platform][group].sort()
            help_text_generated[platform][group] = "\n".join(help_text_list[platform][group])

    return help_text_generated


import_all_commands()

COMMANDS = generate_commands()

HELP_TEXTS = generate_help_text()


def get_text_for_documentation():
    NL = '\n'
    LEFT_QUOTE_NEW = '\['
    RIGHT_QUOTE_NEW = '\]'
    BR = "<br>"
    BR_NL = f"{BR}\n"
    INS = "<ins>"
    INS_END = "</ins>"
    BOLD = "**"
    ITALIC = "_"

    allowed_roles = {
        Role.USER: "всех пользователей",
        Role.MINECRAFT: "майнкрафтеров",
        Role.PALWORLD: "палворлдеров",
        Role.TRUSTED: "доверенных пользователей",
        Role.MODERATOR: "модераторов",
        Role.ADMIN: "админа"
    }

    documentation = []
    for role in allowed_roles:
        commands = filter(
            lambda x: x.access == role and x.name and x.suggest_for_similar and x.help_text and not x.hidden,
            COMMANDS
        )
        commands = sorted(commands, key=lambda y: y.name)
        documentation.append(f"### Команды {allowed_roles[role]}{NL}")
        for cmd in commands:
            cmd: Command
            command_text = f"{BOLD}{INS}{cmd.name.capitalize()}{INS_END}{BOLD} - {cmd.help_text.commands_text}{NL}{BR_NL}"
            if not cmd.help_text.items:
                continue
            help_texts = get_flat_list([
                cmd.help_text.items.get(_role).texts for _role in cmd.help_text.items if _role in allowed_roles
            ])
            help_text_items = []
            for help_text in help_texts:
                if help_text.args:
                    command = f"{BOLD}/{cmd.name.capitalize()} {help_text.args}{BOLD}"
                else:
                    command = f"{BOLD}/{cmd.name.capitalize()}{BOLD}"

                help_text_item = f"{command} - {help_text.description}{NL}"

                help_text_item = help_text_item \
                    .replace('[', LEFT_QUOTE_NEW) \
                    .replace(']', RIGHT_QUOTE_NEW)

                help_text_items.append(help_text_item)

            command_text += BR_NL.join([x for x in help_text_items])
            if cmd.help_text.extra_text:
                command_text += f"{BR_NL}{ITALIC}{cmd.help_text.extra_text.replace(NL + NL, NL).replace(NL, BR_NL)}{ITALIC}{NL}"
            documentation.append(command_text)
    documentation = "\n".join(documentation)
    return documentation
