from copy import copy


class ResponseMessage:
    def __init__(self, msgs, peer_id):
        self.messages = []

        if isinstance(msgs, list):
            for item in msgs:
                rmi = ResponseMessageItem(item, peer_id)
                self.messages.append(rmi)
        else:
            self.messages = [ResponseMessageItem(msgs, peer_id)]


class ResponseMessageItem:
    def __init__(self, msg, peer_id):
        if isinstance(msg, str) or isinstance(msg, int) or isinstance(msg, float):
            msg = {'text': str(msg)}

        msg_copy = copy(msg)

        self.peer_id = peer_id
        self.text = msg_copy.pop('text', "")
        self.attachments = msg_copy.pop('attachments', [])
        if not isinstance(self.attachments, list):
            self.attachments = [self.attachments]
        self.keyboard = msg_copy.pop('keyboard', {})
        self.kwargs = msg_copy
