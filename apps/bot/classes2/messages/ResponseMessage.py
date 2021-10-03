from apps.bot.classes2.messages.ResponseMessageItem import ResponseMessageItem


class ResponseMessage:
    def __init__(self, msgs, peer_id):
        self.messages = []

        if isinstance(msgs, list):
            for item in msgs:
                rmi = ResponseMessageItem(item, peer_id)
                self.messages.append(rmi)
        else:
            self.messages = [ResponseMessageItem(msgs, peer_id)]
