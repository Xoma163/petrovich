from apps.bot.consts import PlatformEnum, RoleEnum
from apps.bot.models import Role
from apps.commands.games.commands.petrovich import Petrovich
from apps.commands.games.commands.wordle import Wordle
from apps.commands.gpt.commands.chatgpt import ChatGPTCommand
from apps.commands.gpt.commands.chatgpt_wtf import WTF
from apps.commands.gpt.commands.grok import GrokCommand
from apps.commands.gpt.commands.grok_wtf import GWTF
from apps.commands.gpt.commands.voice_recognition import VoiceRecognition
from apps.commands.media_command.commands.media_command import Media
from apps.commands.meme.commands.horoscope import Horoscope
from apps.commands.meme.commands.meme import Meme
from apps.commands.meme.commands.memes import Memes
from apps.commands.notifies.commands.notifies import Notifies
from apps.commands.other.commands.birthday import Birthday
from apps.commands.other.commands.calc import Calc
from apps.commands.other.commands.commands import Commands
from apps.commands.other.commands.easy.bye import Bye
from apps.commands.other.commands.easy.git import Git
from apps.commands.other.commands.easy.hi import Hi
from apps.commands.other.commands.easy.thanks import Thanks
from apps.commands.other.commands.help import Help
from apps.commands.other.commands.issue import Issue
from apps.commands.other.commands.minecraft.minecraft_server import Minecraft
from apps.commands.other.commands.moderator.logs import Logs
from apps.commands.other.commands.moderator.roles import Roles
from apps.commands.other.commands.profile import Profile
from apps.commands.other.commands.random import Random
from apps.commands.other.commands.service.actions import Actions
from apps.commands.other.commands.service.check_trusted_role import CheckTrustedRole
from apps.commands.other.commands.service.github_reply import GithubReply
from apps.commands.other.commands.settings import Settings
from apps.commands.other.commands.statistics import Statistics
from apps.commands.other.commands.trusted.audio_track import AudioTrack
from apps.commands.other.commands.trusted.deissue import DeIssue
from apps.commands.other.commands.trusted.trim_video import TrimVideo
from apps.shared.utils.utils import get_flat_list

_commands = [
    # games
    Petrovich,
    Wordle,

    # gpt
    ChatGPTCommand,
    GrokCommand,
    WTF,
    GWTF,
    VoiceRecognition,

    # media
    Media,

    # Meme
    Meme,
    Memes,
    Horoscope,

    # Notifies
    Notifies,

    # other

    # easy
    Bye,
    Git,
    Hi,
    Thanks,

    # minecraft
    Minecraft,

    # Moderator
    Logs,
    Roles,

    # service
    Actions,
    CheckTrustedRole,
    GithubReply,

    # Trusted
    AudioTrack,
    DeIssue,
    TrimVideo,

    # other
    Birthday,
    Calc,
    Commands,
    Help,
    Issue,
    Profile,
    Random,
    Settings,
    Statistics,
]

_accept_extra_commands = [
    VoiceRecognition,
    Media
]


def get_sorted_commands(cmds):
    _cmds = [_cmd() for _cmd in cmds]
    return sorted(_cmds, key=lambda x: x.priority, reverse=True)


def generate_help_text(cmds):
    roles = list(Role.objects.values_list("name", flat=True))
    platform_help = {
        platform: {role: [] for role in roles}
        for platform in PlatformEnum
    }

    for command in cmds:
        if not command.help_text:
            continue
        entry = f"{command.name.capitalize()} - {command.help_text.commands_text}"
        role_name = command.access.name
        for platform in command.platforms:
            if role_name in platform_help[platform]:
                platform_help[platform][role_name].append(entry)

    return {
        platform: {
            role: "\n".join(sorted(entries))
            for role, entries in role_map.items()
        }
        for platform, role_map in platform_help.items()
    }


def get_text_for_documentation(cmds):
    NL = '\n'
    BR = "<br>"
    BR_NL = f"{BR}\n"
    INS, INS_END = "<ins>", "</ins>"
    BOLD, ITALIC = "**", "_"
    LEFT_QUOTE, RIGHT_QUOTE = r'\[', r'\]'

    allowed_roles = {
        RoleEnum.USER: "всех пользователей",
        RoleEnum.MINECRAFT: "майнкрафтеров",
        RoleEnum.TRUSTED: "доверенных пользователей",
        RoleEnum.MODERATOR: "модераторов",
        RoleEnum.ADMIN: "админа",
    }

    documentation = []
    for role, title in allowed_roles.items():
        documentation.append(f"### Команды {title}{NL}")
        role_cmds = sorted(
            (
                cmd for cmd in cmds
                if (
                    cmd.access == role
                    and cmd.name
                    and cmd.help_text
            )
            ),
            key=lambda c: c.name,
        )

        for cmd in role_cmds:
            name_cap = cmd.name.capitalize()
            base = f"{BOLD}{INS}{name_cap}{INS_END}{BOLD} - {cmd.help_text.commands_text}{NL}{BR_NL}"
            help_texts = get_flat_list([
                cmd.help_text.help_texts.get(r).items
                for r in cmd.help_text.help_texts
                if r in allowed_roles
            ])
            if not help_texts:
                continue

            items = []
            for item in help_texts:
                command_name = f"{name_cap} {item.args}" if item.args else name_cap
                command = f"{BOLD}/{command_name}{BOLD}"
                text = f"{command} - {item.description}{NL}"
                items.append(
                    text.replace('[', LEFT_QUOTE).replace(']', RIGHT_QUOTE)
                )

            block = base + BR_NL.join(items)
            if cmd.help_text.extra_text:
                extra = cmd.help_text.extra_text.replace(NL + NL, NL).replace(NL, BR_NL)
                block += f"{BR_NL}{ITALIC}{extra}{ITALIC}{NL}"
            documentation.append(block)

    return "\n".join(documentation)


registry_commands = get_sorted_commands(_commands)
registry_accept_extra_commands = get_sorted_commands(_accept_extra_commands)
registry_help_texts = generate_help_text(registry_commands)
documentation_text = get_text_for_documentation(registry_commands)
