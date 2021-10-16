from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.classes.Command import Command
from apps.bot.utils.utils import get_role_by_str


class Who(Command):
    name = "кто"
    help_text = "присылает список людей с определённой ролью в конфе"
    help_texts = [
        "(N) - присылает список людей с ролью N в данной конфе\n",
        "Доступные роли: админ, админ конфы, доверенный, модератор, майнкрафт, майнкрафт уведомления, террария, дом, забанен.\n",
        "Чтобы узнать свои права существует команда /права"
    ]
    conversation = True
    args = 1
    platforms = [Platform.VK, Platform.TG]

    def start(self):
        arg = self.event.message.args_str.lower()
        role = get_role_by_str(arg)
        if arg in ['админ конфы', 'админ беседы', 'админ конференции', 'админ чата', 'администратор конфы',
                   'администратор беседы', 'администратор конференции', 'администратор чата']:
            return str(self.event.chat.admin)
        elif arg in ['пидор']:
            return "ты"
        elif not role:
            raise PWarning("Не знаю такой роли")
        users = self.get_users(self.event.chat, role)
        if len(users) == 0:
            raise PWarning("Нет людей с данной ролью")
        users_list = [str(user) for user in users]
        result = "\n".join(users_list)
        return str(result)

    def get_users(self, chat, role):
        params = {'chats': chat, 'groups__name': role.name}
        return list(self.bot.user_model.filter(**params))
