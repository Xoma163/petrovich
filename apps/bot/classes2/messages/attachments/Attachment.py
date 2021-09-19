class Attachment:
    def __init__(self, att_type):
        self.type = att_type
        self.download_url = None
        self.private_download_url = None
        self.content = None
