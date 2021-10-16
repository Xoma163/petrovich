class Attachment:

    def __init__(self, att_type):
        self.type = att_type
        self.public_download_url = None
        self.private_download_url = None
        self.content = None
        self.size = None

    def set_private_download_url_tg(self, tg_bot, file_id):
        file_path = tg_bot.requests.get('getFile', params={'file_id': file_id}).json()['result']['file_path']
        self.private_download_url = f'https://{tg_bot.API_TELEGRAM_URL}/file/bot{tg_bot.token}/{file_path}'
