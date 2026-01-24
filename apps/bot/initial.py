import importlib
import os
import pkgutil

from django.contrib.auth.models import Group

from apps.bot.consts import Platform, RoleEnum
from apps.commands.command import Command, AcceptExtraCommand
from apps.shared.utils.utils import get_flat_list
from petrovich.settings import BASE_DIR


def import_all_commands():
    commands_folders = [
        os.path.join(BASE_DIR, "apps", "bot", "commands"),
        os.path.join(BASE_DIR, "apps", "commands", "gpt"),
        os.path.join(BASE_DIR, "apps", "commands", "games"),
        os.path.join(BASE_DIR, "apps", "commands", "media_command"),
        os.path.join(BASE_DIR, "apps", "commands", "meme"),
        os.path.join(BASE_DIR, "apps", "commands", "notifies"),
        os.path.join(BASE_DIR, "apps", "commands", "other")
    ]
    commands_dirs = []
    for commands_folder in commands_folders:
        for path in os.walk(commands_folder):
            if not path[0].endswith('__pycache__'):
                commands_dirs.append(path[0])

    for (module_loader, name, _) in pkgutil.iter_modules(commands_dirs):
        package = module_loader.path.replace(BASE_DIR, '')[1:].replace('/', '.')
        importlib.import_module('.' + name, package)

def generate_commands(base_class=Command):
    commands = base_class.__subclasses__()
    new_commands = commands
    flag = True
    while flag:
        new_commands = [x for x in [cls.__subclasses__() for cls in new_commands] if x]  # noqa
        if new_commands:
            _new_commands = []
            for cmd in new_commands:
                _new_commands += cmd
            commands += _new_commands
            new_commands = _new_commands
        else:
            flag = False
    commands = [x() for x in commands if (
            x.__module__.startswith('apps.bot.commands') or
            x.__module__.startswith('apps.commands.gpt') or
            x.__module__.startswith('apps.commands.games') or
            x.__module__.startswith('apps.commands.media_command') or
            x.__module__.startswith('apps.commands.meme') or
            x.__module__.startswith('apps.commands.notifies') or
            x.__module__.startswith('apps.commands.other')
    ) and x.enabled and not x.abstract]
    commands.sort(key=lambda x: x.priority, reverse=True)
    return commands


def generate_help_text():
    groups = [x['name'] for x in Group.objects.all().values('name')]
    help_text_generated = {p: dict.fromkeys(groups, "") for p in Platform}
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
            help_text_generated[platform][group] = "\n".join(help_text_list[platform][group])  # noqa

    return help_text_generated


import_all_commands()

COMMANDS = generate_commands(Command)

EXTRA_COMMANDS = generate_commands(AcceptExtraCommand)

HELP_TEXTS = generate_help_text()


def get_text_for_documentation():
    NL = '\n'
    LEFT_QUOTE_NEW = r'\['
    RIGHT_QUOTE_NEW = r'\]'
    BR = "<br>"
    BR_NL = f"{BR}\n"
    INS = "<ins>"
    INS_END = "</ins>"
    BOLD = "**"
    ITALIC = "_"

    allowed_roles = {
        RoleEnum.USER: "всех пользователей",
        RoleEnum.MINECRAFT: "майнкрафтеров",
        RoleEnum.TRUSTED: "доверенных пользователей",
        RoleEnum.MODERATOR: "модераторов",
        RoleEnum.ADMIN: "админа",
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
            if not cmd.help_text.help_texts:
                continue
            help_texts = get_flat_list([
                cmd.help_text.help_texts.get(_role).items for _role in cmd.help_text.help_texts if
                _role in allowed_roles
            ])
            help_text_items = []
            for help_text in help_texts:
                _command = f"{cmd.name.capitalize()} {help_text.args}" if help_text.args else cmd.name.capitalize()
                command = f"{BOLD}/{_command}{BOLD}"

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
