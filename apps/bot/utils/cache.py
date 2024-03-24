from django.core.cache import cache


class MessagesCache:
    PRE_KEY = 'messages'

    """
    Структура хранения сообщений:
    {
      peer_id: {
        message_id_1: {
          *message_body*
        },
        message_id_2: {
          *message_body*
        }
      }
    }
    """

    def __init__(self, peer_id: int):
        self.peer_id: int = peer_id
        self.cache = cache

    def _get_key(self):
        return f"{self.PRE_KEY}_{self.peer_id}"

    def add_message(self, message_id, message) -> None:
        if not self.peer_id:
            return
        if not message_id:
            return

        data = self.get_messages()
        if message_id in data:
            return
        data[message_id] = message
        self.cache.set(self._get_key(), data, timeout=None)

    def clear(self) -> None:
        self.cache.clear()

    def get_messages(self) -> dict:
        return self.cache.get(self._get_key(), {})


class PollCache:
    PRE_KEY = 'poll'

    def _get_key(self):
        return f"{self.PRE_KEY}_{self.poll_id}"

    def __init__(self, poll_id):
        self.poll_id = poll_id
        self.cache = cache

    def add_poll(self, data) -> None:
        poll = self.get_poll()
        if poll:
            return
        self.cache.set(self._get_key(), data, timeout=None)

    def clear(self) -> None:
        self.cache.clear()

    def get_poll(self) -> dict:
        return self.cache.get(self._get_key())
