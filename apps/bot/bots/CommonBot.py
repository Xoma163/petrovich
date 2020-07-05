import threading

from apps.bot.classes.VkEvent import VkEvent


class CommonBot():
    def __init__(self):
        self.mentions = []

    def run(self):
        self.listen()

    def listen(self):
        pass

    def send_message(self, peer_id, msg="ᅠ", attachments=None, keyboard=None, dont_parse_links=False, **kwargs):
        pass

    @staticmethod
    def parse_message(peer_id, result):
        if isinstance(result, str) or isinstance(result, int) or isinstance(result, float):
            result = {'msg': result}
        if isinstance(result, dict):
            result = [result]
        if isinstance(result, list):
            for msg in result:
                if isinstance(msg, str):
                    msg = {'msg': msg}
                if isinstance(msg, dict):
                    return msg

    def parse_and_send_msgs(self, peer_id, result):
        msg = self.parse_message(peer_id, result)
        self.send_message(peer_id, **msg)

    # Отправляет сообщения юзерам в разных потоках
    def parse_and_send_msgs_thread(self, chat_ids, message):
        if not isinstance(chat_ids, list):
            chat_ids = [chat_ids]
        for chat_id in chat_ids:
            thread = threading.Thread(target=self.parse_and_send_msgs, args=(chat_id, message,))
            thread.start()

    def need_a_response(self, event):
        message = event['message']['text']
        from_user = event['from_user']
        have_audio_message = self.have_audio_message(event)
        if have_audio_message:
            return True
        have_action = event['message']['action'] is not None
        if have_action:
            return True
        if len(message) == 0:
            return False
        if from_user:
            return True
        if message[0] == '/':
            return True
        for mention in self.mentions:
            if message.find(mention) != -1:
                return True
        return False

    @staticmethod
    def have_audio_message(vk_event):
        if isinstance(vk_event, VkEvent):
            all_attachments = vk_event.attachments or []
            if vk_event.fwd:
                all_attachments += vk_event.fwd[0]['attachments']
            if all_attachments:
                for attachment in all_attachments:
                    if attachment['type'] == 'audio_message':
                        return True
        else:
            all_attachments = vk_event['message']['attachments'].copy()
            if vk_event['fwd']:
                all_attachments += vk_event['fwd'][0]['attachments']
            if all_attachments:
                for attachment in all_attachments:
                    if attachment['type'] == 'audio_message':
                        # Костыль, чтобы при пересланном сообщении он не выполнял никакие другие команды
                        # vk_event['message']['text'] = ''
                        return True
        return False

    def get_user_by_id(self, user_id):
        pass

    @staticmethod
    def parse_date(date):
        date_arr = date.split('.')
        if len(date_arr) == 2:
            return f"1970-{date_arr[1]}-{date_arr[0]}"
        else:
            return f"{date_arr[2]}-{date_arr[1]}-{date_arr[0]}"
