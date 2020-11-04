from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand


class Online(CommonCommand):
    def __init__(self):
        names = ["онлайн"]
        help_text = "Онлайн - присылает список пользователей онлайн в конфе"
        super().__init__(names, help_text, conversation=True, platforms=[Platform.VK])

    def start(self):
        users = sorted(self.bot.get_conference_users(self.event.chat.chat_id), key=lambda x: x['first_name'])
        online_users_name = []
        for user in users:
            if user['online']:
                online_users_name.append(f"{user['first_name']} {user['last_name']}")
        if not online_users_name:
            return "Нет пользователей онлайн"
        online_users_str = "\n".join(online_users_name)
        return f"Пользователи онлайн в конфе:\n\n" \
               f"{online_users_str}"
