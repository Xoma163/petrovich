from apps.bot.classes2.messages.Message import Message


class Event:
    def __init__(self):
        self.is_from_user = False
        self.is_from_chat = False
        self.is_mentioned = False
        self.is_from_bot = False

        self.sender = None
        self.chat = None
        self.peer_id = None
        self.platform = None

        self.payload = None
        self.action = None

        self.message: Message = None
        self.fwd: list = []
        self.attachments: list = []

    def parse(self):
        raise NotImplementedError

    # def need_a_response(self):
    #     pass
    #
    # def setup_event_before(self):
    #     pass
    #
    # def setup_event_after(self):
    #     pass
    #
    # def setup_event(self):
    #     self.setup_event_before()
    #     if not self.need_a_response():
    #         return
    #     self.setup_event_after()
    #
