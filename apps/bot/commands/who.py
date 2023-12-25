from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile
from apps.bot.utils.utils import get_role_by_str


class Who(Command):
    name = "кто"

    help_text = HelpText(
        commands_text="присылает список людей с определённой ролью в конфе",
        extra_text=(
            "Доступные роли: админ, доверенный, модератор, майнкрафт, майнкрафт уведомления, террария, забанен\n"
            "Чтобы узнать свои права существует команда /права"
        ),
        help_texts=[
            HelpTextItem(Role.USER, [
                "(N) - присылает список людей с ролью N в данной конфе"
            ])
        ]
    )

    conversation = True
    args = 1
    platforms = [Platform.TG]
    mentioned = True

    bot: TgBot

    def start(self) -> ResponseMessage:
        arg = self.event.message.args_str
        role = get_role_by_str(arg)
        if arg in ['пидор']:
            answer = "ты"
            return ResponseMessage(ResponseMessageItem(text=answer))
        elif arg in ['петрович']:
            answer = "я"
            return ResponseMessage(ResponseMessageItem(text=answer))
        elif not role:
            raise PWarning("Не знаю такой роли")
        users = self.get_users(self.event.chat, role)
        if len(users) == 0:
            raise PWarning("Нет людей с данной ролью")
        users_list = [str(user) for user in users]
        result = "\n".join(users_list)
        answer = str(result)
        return ResponseMessage(ResponseMessageItem(text=answer))

    @staticmethod
    def get_users(chat, role):
        params = {'chats': chat, 'groups__name': role.name}
        return list(Profile.objects.filter(**params))
