from apps.bot.classes.Consts import Platform
from apps.bot.classes2.messages.Message import Message
from apps.bot.models import Users, Chat


class Event:
    def __init__(self, raw_event):
        self.raw = raw_event  # json

        self.is_from_user: bool = False
        self.is_from_bot: bool = False
        self.is_from_chat: bool = False

        self.is_mentioned: bool = False

        self.sender: Users = None
        self.chat: Chat = None
        self.peer_id: str = None
        self.platform: Platform = None

        self.payload: dict = {}
        self.action = None

        self.message: Message = None
        self.fwd: list = []
        self.attachments: list = []

        self.force_need_a_response: bool = False

    def setup_event(self, bot):
        raise NotImplementedError

    # ToDo: проверка на забаненых
    def need_a_response(self):
        if self.force_need_a_response:
            return True
        # some logic
        if self.message is None:
            return False
        return True
