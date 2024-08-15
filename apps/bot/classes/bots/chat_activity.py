import threading
import time

from django.core.cache import cache

from apps.bot.classes.const.activities import ActivitiesEnum


class ChatActivity:
    def __init__(self, bot, activity: ActivitiesEnum, peer_id, send_chat_action=True):
        self.bot = bot
        self.activity: ActivitiesEnum = activity
        self.peer_id = peer_id
        self.send_chat_action: bool = send_chat_action
        self._activity_flag: bool = False

    def __enter__(self):
        self.set_activity_thread()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_activity_thread()

    def set_activity_thread(self):
        if not self.send_chat_action:
            return
        if not self.peer_id or not self.activity:
            return
        if self._activity_flag:
            return
        if cache.get(f"activity_{self.peer_id}"):
            return

        cache.set(f"activity_{self.peer_id}", True)
        self._activity_flag = True
        threading.Thread(
            target=self._set_activity_thread,
        ).start()

    def stop_activity_thread(self):
        self._activity_flag = False
        cache.delete(f"activity_{self.peer_id}")

    def _set_activity_thread(self):
        while self._activity_flag and cache.get(f"activity_{self.peer_id}"):
            self.bot.set_activity(self.peer_id, self.activity)
            time.sleep(5)
