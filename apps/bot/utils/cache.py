from django.core.cache import cache


class MessagesCache:
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

    def add_message(self, message_id, message) -> None:
        if not self.peer_id:
            return
        if not message_id:
            return

        data = self.cache.get(self.peer_id, {})
        if message_id in data:
            return
        data[message_id] = message
        self.cache.set(self.peer_id, data, timeout=None)

    def clear(self) -> None:
        self.cache.clear()

    def get_messages(self) -> dict:
        return self.cache.get(self.peer_id, {})
