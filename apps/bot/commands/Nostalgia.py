import json
import random
from io import BytesIO

from apps.bot.classes.Consts import Platform, Role
from apps.bot.classes.QuotesGenerator import QuotesGenerator
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.models import Users


class Nostalgia(CommonCommand):
    name = "ностальгия"
    names = ["ностальжи", "(с)"]
    help_text = "генерирует картинку с сообщениями из конфы беседки мразей"
    access = Role.MRAZ

    def start(self):
        with open('secrets/mrazi_chats/mrazi1.json', 'r') as file:
            content = file.read()
        data = json.loads(content)

        msgs_count = 20
        start_pos = random.randint(0, len(data) - msgs_count)
        msgs = data[start_pos:start_pos + msgs_count]
        msgs_parsed = self.prepare_msgs_for_quote_generator(msgs)

        qg = QuotesGenerator()
        pil_image = qg.build(msgs_parsed, title="Ностальгия")
        bytes_io = BytesIO()
        pil_image.save(bytes_io, format='PNG')
        if pil_image.height > 1500:
            attachments = self.bot.upload_document(bytes_io, self.event.peer_id, "Ностальгия", filename="nostalgia.png")
        else:
            attachments = self.bot.upload_photos(bytes_io)
        return {"msg": msgs[0]['datetime'], "attachments": attachments}

    def prepare_msgs_for_quote_generator(self, msgs):
        new_msgs = []
        users_avatars = {}
        for msg in msgs:
            message = {'text': msg['text']}
            for att in msg['attachments']:
                if att['type'] == "Фотография":
                    message['photo'] = att['link']
                if att['type'] in ["Видеозапись", "Файл", "Ссылка"]:
                    message['text'] += f'\n{att["link"]}'
                if msg['fwd']:
                    message['text'] += '\n(Пересланные сообщения)\n'

            if msg['author'] not in users_avatars:
                name, surname = msg['author'].split(' ', 1)
                vk_user = Users.objects.filter(name=name, surname=surname, platform=Platform.VK.name).first()
                if vk_user:
                    users_avatars[msg['author']] = vk_user.avatar
            avatar = users_avatars.get(msg['author'], None)

            new_msg = {'username': msg['author'], 'message': message, 'avatar': avatar}
            new_msgs.append(new_msg)
        return new_msgs
