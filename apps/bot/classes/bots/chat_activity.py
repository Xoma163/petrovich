from apps.bot.classes.const.activities import ActivitiesEnum


class ChatActivity:
    def __init__(self, bot: "Bot", activity: ActivitiesEnum, peer_id, send_chat_action=True):
        self.bot = bot
        self.activity = activity
        self.peer_id = peer_id
        self.send_chat_action = send_chat_action

    def __enter__(self):
        self.bot.set_activity_thread(self.peer_id, self.activity)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bot.stop_activity_thread(self.peer_id)
