from io import BytesIO

from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.utils.QuotesGenerator import QuotesGenerator


# Design by M.Marchukov and M.Marchukova
# https://www.figma.com/file/yOqhSHOtYX76GcEJ3yB4oH/Bot?node-id=33%3A15
class Quote(Command):
    name = "цитата"
    help_text = "генерирует картинку с цитатой"
    help_texts = ["(Пересылаемые сообщение) - генерирует картинку с цитатой"]
    fwd = True
    platforms = [Platform.TG]

    bot: TgBot

    def start(self):
        msgs = self.parse_fwd(self.event.fwd)

        qg = QuotesGenerator()
        pil_image = qg.build(msgs, "Сохры")
        bytes_io = BytesIO()
        pil_image.save(bytes_io, format='PNG')
        if pil_image.height > 1500:
            attachments = self.bot.get_document_attachment(bytes_io, self.event.peer_id, filename="petrovich_quote.png")
        else:
            attachments = self.bot.get_photo_attachment(bytes_io, peer_id=self.event.peer_id,
                                                        filename="petrovich_quote.png")
        return {"attachments": attachments}

    def parse_fwd(self, fwd_messages):
        msgs = []
        next_append = False
        for msg in fwd_messages:
            message = {'text': msg.message.raw.replace('\n', '▲ ▲') if msg.message and isinstance(msg.message.raw,
                                                                                                  str) else ''}

            if msg.is_from_user:
                username = str(msg.sender)
                avatar = msg.sender.avatar
                if not avatar and self.event.platform in [Platform.TG]:
                    self.bot.update_profile_avatar(self.event.sender, msg.from_id)
            else:
                quote_bot = self.bot.get_bot_by_id(msg.from_id)
                username = str(quote_bot)
                avatar = quote_bot.avatar
            if msg.attachments:
                photo = msg.attachments[0]
                if isinstance(photo, PhotoAttachment):
                    message['photo'] = photo.download_content()

                # sticker = msg.attachments[0]
                # if isinstance(sticker, StickerAttachment):
                #     message['photo'] = sticker.url

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

            if msg.fwd:
                msgs[-1]['fwd'] = self.parse_fwd(msg.fwd)
                next_append = True

        return msgs
