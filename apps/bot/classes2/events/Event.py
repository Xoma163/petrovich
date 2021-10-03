from apps.bot.classes2.messages.Message import Message


class Event:
    def __init__(self, raw_event):
        self.raw = raw_event  # json

        self.is_from_user = False
        self.is_from_bot = False
        self.is_from_chat = False

        self.is_mentioned = False

        self.sender = None
        self.chat = None
        self.peer_id = None
        self.platform = None

        self.payload = None
        self.action = None

        self.message: Message = None
        self.fwd: list = []
        self.attachments: list = []

        self.force_need_a_response = False

    def setup_event(self, bot):
        raise NotImplementedError

    # ToDo: проверка на забаненых
    def need_a_response(self):
        if self.force_need_a_response:
            return True
        return True
