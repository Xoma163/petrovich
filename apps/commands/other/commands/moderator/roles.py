from apps.bot.consts import RoleEnum
from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.bot.core.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile
from apps.bot.utils import get_profile_by_name
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.shared.exceptions import PWarning
from apps.shared.utils.utils import get_role_by_str


class Roles(Command):
    name = "роль"
    names = ["роли"]
    access = RoleEnum.MODERATOR
    help_text = HelpText(
        commands_text="добавление и удаление ролей пользователю",
        help_texts=[
            HelpTextItem(
                RoleEnum.MODERATOR,
                [
                    HelpTextArgument("список", "показывает доступные для управления роли"),
                    HelpTextArgument("добавить (пользователь) (роль)", "добавляет роль пользователю"),
                    HelpTextArgument("удалить (пользователь) (роль)", "удаляет роль пользователю"),
                ],
            )
        ],
    )
    conversation = True

    bot: TgBot

    def start(self) -> ResponseMessage:
        manageable_roles = self.get_manageable_roles()
        if not self.event.message.args or self.event.message.args == ["список"]:
            roles = "\n".join(f"- {role}" for role in manageable_roles)
            return ResponseMessage(ResponseMessageItem(f"Доступные для добавления и удаления роли:\n{roles}"))

        try:
            action, username, role_str = self.event.message.args_str.split(" ", 2)
        except ValueError:
            raise PWarning("Проверьте синтаксис команды. Ожидаются действие, пользователь и роль")

        profile = get_profile_by_name([username], self.event.chat)
        role = get_role_by_str(role_str)
        if role is None:
            raise PWarning(f"Я не знаю роли {role_str}")

        if role not in manageable_roles:
            raise PWarning(f'Нельзя добавлять/удалять роль "{role}"')

        if action == "добавить":
            rmi = self.add_role(profile, role)
        elif action == "удалить":
            rmi = self.remove_role(profile, role)
        else:
            raise PWarning(f'Неизвестное действие - "{action}"')
        return ResponseMessage(rmi)

    def get_manageable_roles(self) -> list[RoleEnum]:
        roles = [RoleEnum.MINECRAFT, RoleEnum.TRUSTED]
        if self.event.sender.check_role(RoleEnum.ADMIN):
            roles.insert(0, RoleEnum.MODERATOR)
        return roles

    @staticmethod
    def add_role(profile: Profile, role: RoleEnum) -> ResponseMessageItem:
        if profile.check_role(role):
            raise PWarning(f'У пользователя уже есть роль "{role}"')
        profile.add_role(role)
        return ResponseMessageItem(f'Добавил пользователю "{profile}" роль "{role}"')

    @staticmethod
    def remove_role(profile: Profile, role: RoleEnum) -> ResponseMessageItem:
        if not profile.check_role(role):
            raise PWarning(f'У пользователя нет роли "{role}"')
        profile.remove_role(role)
        return ResponseMessageItem(f'Удалил пользователю "{profile}" роль "{role}"')
