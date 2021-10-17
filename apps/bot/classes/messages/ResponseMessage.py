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

        if isinstance(msg, dict):
            self.peer_id = peer_id
            self.text = msg.get('text', "")
            self.attachments = msg.get('attachments', [])
            if not isinstance(self.attachments, list):
                self.attachments = [self.attachments]
            self.keyboard = msg.get('keyboard', {})
            self.dont_parse_links = msg.get('dont_parse_links', False)
