class Fwd:
    def __init__(self, fwd):
        self.messages = []


class FwdMessage:
    def __init__(self, message, attachments=None):
        self.message = message
        self.attachments = attachments
