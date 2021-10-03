class ResponseMessageItem:

    def __init__(self, msg, peer_id):
        if isinstance(msg, str) or isinstance(msg, int) or isinstance(msg, float):
            msg = {'text': str(msg)}

        if isinstance(msg, dict):
            self.peer_id = peer_id
            self.text = msg.get('text', None)
            self.attachments = msg.get('attachments', None)
            self.keyboard = msg.get('keyboard', None)
            self.dont_parse_links = msg.get('dont_parse_links', False)
