from django.core.cache import cache


class MessagesCache:
    PRE_KEY = "messages"

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
        if not message_id:
            return

        data = self.get_messages()
        if message_id in data:
            return
        data[message_id] = message
        self.cache.set(self._get_key(), data, timeout=None)

    def set_message(self, message_id, message):
        if not message_id:
            return

        data = self.get_messages()
        data[message_id] = message
        self.cache.set(self._get_key(), data, timeout=None)

    def clear(self) -> None:
        self.cache.clear()

    def get_messages(self) -> dict:
        return self.cache.get(self._get_key(), {})


class GPTResponsesCache:
    PRE_KEY = "gpt_responses"

    """
    Структура хранения респонсов:
    {
      chatgpt_peer_id: {
        message_id_1: [
          *response_body*
        ]
        message_id_2: [
          *response_body*
        ]
      }
    }
    """

    def __init__(self, gpt_provider: str, peer_id: int):
        self.gpt_provider: str = gpt_provider
        self.peer_id: int = peer_id

        self.cache = cache

    def _get_key(self):
        return f"{self.PRE_KEY}_{self.gpt_provider}_{self.peer_id}"

    def add_response(self, message_id, response) -> None:
        data = self.get_responses()
        if message_id in data:
            return
        data[message_id] = response
        self.cache.set(self._get_key(), data, timeout=None)

    def set_response(self, message_id, response: list[dict]):
        if not message_id:
            return

        data = self.get_responses()
        data[message_id] = response
        self.cache.set(self._get_key(), data, timeout=None)

    def clear(self) -> None:
        self.cache.clear()

    def get_responses(self) -> dict:
        return self.cache.get(self._get_key(), {})
