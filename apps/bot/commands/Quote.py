from io import BytesIO

from apps.bot.classes.Command import Command
# Design by M.Marchukov and M.Marchukova
# https://www.figma.com/file/yOqhSHOtYX76GcEJ3yB4oH/Bot?node-id=33%3A15
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform
from apps.bot.utils.QuotesGenerator import QuotesGenerator


class Quote(Command):
    name = "цитата"
    names = ["(c)", "(с)"]
    help_text = "генерирует картинку с цитатой"
    help_texts = ["(Пересылаемые сообщение) - генерирует картинку с цитатой"]
    fwd = True
    platforms = [Platform.VK]

    def start(self):
        self.bot.set_activity(self.event.peer_id, ActivitiesEnum.UPLOAD_PHOTO)

        msgs = self.parse_fwd(self.event.fwd)

        qg = QuotesGenerator()
        pil_image = qg.build(msgs, "Сохры")
        bytes_io = BytesIO()
        pil_image.save(bytes_io, format='PNG')
        if pil_image.height > 1500:
            attachments = self.bot.upload_document(bytes_io, self.event.peer_id, "Сохры", filename="quote.png")
        else:
            attachments = self.bot.upload_photos(bytes_io)
        return {"attachments": attachments}

    def parse_fwd(self, fwd_messages):
        msgs = []
        next_append = False
        for msg in fwd_messages:
            message = {'text': msg['text'].replace('\n', '▲ ▲') if isinstance(msg['text'], str) else msg['text']}

            if msg['from_id'] > 0:
                quote_user = self.bot.get_user_by_id(msg['from_id'])
                username = str(quote_user)
                avatar = quote_user.avatar
                if not avatar:
                    self.bot.update_user_avatar(msg['from_id'])
            else:
                quote_bot = self.bot.get_bot_by_id(msg['from_id'])
                username = str(quote_bot)
                avatar = quote_bot.avatar
                if not avatar:
                    self.bot.update_bot_avatar(msg['from_id'])
            if msg.get('attachments'):
                photo = msg['attachments'][0].get('photo')
                if photo:
                    max_photo = self.event.get_max_size_image(photo)
                    message['photo'] = max_photo['url']

                sticker = msg['attachments'][0].get('sticker')
                if sticker:
                    image = self.event.get_sticker_128(sticker['images'])
                    message['photo'] = image['url']

            # stack messages from one user
            if msgs and msgs[-1]['username'] == username:
                if next_append:
                    msgs.append({'username': username, 'message': message, 'avatar': avatar})
                    next_append = 'photo' in message
                elif 'photo' in message:
                    msgs[-1]['message']['photo'] = message['photo']
                    msgs[-1]['message']['text'] += f"▲ ▲{message['text']}"
                    next_append = True
                else:
                    msgs[-1]['message']['text'] += f"▲ ▲{message['text']}"
            else:
                next_append = False
                msgs.append({'username': username, 'message': message, 'avatar': avatar})
                if 'photo' in message:
                    next_append = True

            if msg.get('fwd'):
                fwd = msg['fwd'] if isinstance(msg['fwd'], list) else [msg['fwd']]
                msgs[-1]['fwd'] = self.parse_fwd(fwd)
                next_append = True

        return msgs
