import threading
import time

from django.core.cache import cache

from apps.bot.core.chat_actions import ChatActionEnum


class ChatActionSender:
    def __init__(self, bot, chat_action: ChatActionEnum, peer_id, send_chat_action=True):
        self.bot = bot
        self.chat_action: ChatActionEnum = chat_action
        self.peer_id = peer_id
        self.send_chat_action: bool = send_chat_action
        self._chat_action_flag: bool = False

    def __enter__(self):
        self.set_chat_action_thread()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_chat_action_thread()

    def set_chat_action_thread(self):
        if not self.send_chat_action:
            return
        if not self.peer_id or not self.chat_action:
            return
        if self._chat_action_flag:
            return
        if cache.get(self.__get_key()):
            return

        cache.set(self.__get_key(), True)
        self._chat_action_flag = True
        threading.Thread(
            target=self._set_chat_action_thread,
        ).start()

    def stop_chat_action_thread(self):
        self._chat_action_flag = False
        cache.delete(self.__get_key())

    def _set_chat_action_thread(self):
        while self._chat_action_flag and cache.get(self.__get_key()):
            self.bot.set_chat_action(self.peer_id, self.chat_action)
            time.sleep(5)

    def __get_key(self):
        return f"chat_action_{self.peer_id}"
