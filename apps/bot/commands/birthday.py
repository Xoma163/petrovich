import datetime

from apps.bot.classes.command import Command
from apps.bot.classes.help_text import HelpText
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Birthday(Command):
    name = "др"

    help_text = HelpText(
        commands_text="выводит список участников отсортированный по дате рождения"
    )
    conversation = True

    def start(self) -> ResponseMessage:
        users = self.event.chat.users.filter(birthday__isnull=False).order_by('birthday__month', 'birthday__day')

        this_year_birthday_people = []
        next_year_birthday_people = []
        dt_now = datetime.datetime.now().date()
        for user in users:
            if user.birthday.month <= dt_now.month and user.birthday.day < dt_now.day:
                next_year_birthday_people.append(user)
            else:
                this_year_birthday_people.append(user)

        result = self.generate_users_birthday(this_year_birthday_people, dt_now.year)
        if result:
            result.append("")
        result += self.generate_users_birthday(next_year_birthday_people, dt_now.year + 1)

        answer = "\n".join(result)
        return ResponseMessage(ResponseMessageItem(answer))

    @staticmethod
    def generate_users_birthday(users, year):
        result = []
        if users:
            result.append(f"{year}:")
        for user in users:
            if not user.settings.celebrate_bday:
                continue
            result.append(f"{user.birthday.strftime('%d.%m')} — {user}")
        return result
