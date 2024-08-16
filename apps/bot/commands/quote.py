import time
from io import BytesIO

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.event.tg_event import TgEvent
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.cache import MessagesCache
from apps.bot.utils.quotes_generator import QuotesGenerator


# Design by M.Marchukov and M.Marchukova
# https://www.figma.com/file/yOqhSHOtYX76GcEJ3yB4oH/Bot?node-id=33%3A15
class Quote(Command):
    name = "цитата"

    help_text = HelpText(
        commands_text="генерирует картинку с цитатой",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("(Пересылаемые сообщение)", "генерирует картинку с цитатой")
            ])
        ]
    )
    platforms = [Platform.TG]

    bot: TgBot

    SPECIAL_SYMBOLS = "▲ ▲"

    def start(self) -> ResponseMessage:
        if self.event.fwd:
            messages = self.event.fwd
        elif self.event.payload:
            time.sleep(2)
            mc = MessagesCache(self.event.peer_id)
            all_messages = mc.get_messages()
            sorted_messages = {x: all_messages[x] for x in all_messages if x > self.event.message.id}
            messages = [TgEvent(x[1]) for x in sorted(sorted_messages.items(), key=lambda x: x[0])]
            for event in messages:
                event.setup_event(is_fwd=True)
        else:
            button = self.bot.get_button("Цитата", command=self.name)
            keyboard = self.bot.get_inline_keyboard([button])
            answer = "Перешлите сообщения после моего и нажмите кнопку, чтобы сделать цитату"
            return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard))

        msgs = self.parse_fwd(messages)

        qg = QuotesGenerator()
        pil_image = qg.build(msgs, "Цитата")
        bytes_io = BytesIO()
        pil_image.save(bytes_io, format='PNG')
        if pil_image.height > 1500:
            attachment = self.bot.get_document_attachment(bytes_io, self.event.peer_id, filename="petrovich_quote.png")
            attachment.set_thumbnail(attachment.content)
        else:
            attachment = self.bot.get_photo_attachment(bytes_io, peer_id=self.event.peer_id,
                                                       filename="petrovich_quote.png")
        return ResponseMessage(ResponseMessageItem(attachments=[attachment]))

    def parse_fwd(self, fwd_messages):
        msgs = []
        next_append = False
        for msg in fwd_messages:
            message = {'text': msg.message.raw.replace('\n', self.SPECIAL_SYMBOLS) if msg.message and isinstance(
                msg.message.raw, str) else ''}

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
                    message['photo'] = photo.download_content(self.event.peer_id)

            # stack messages from one user
            if msgs and msgs[-1]['username'] == username:
                if next_append:
                    msgs.append({'username': username, 'message': message, 'avatar': avatar})
                    next_append = 'photo' in message
                elif 'photo' in message:
                    msgs[-1]['message']['photo'] = message['photo']
                    msgs[-1]['message']['text'] += f"{self.SPECIAL_SYMBOLS}{message['text']}"
                    next_append = True
                else:
                    msgs[-1]['message']['text'] += f"{self.SPECIAL_SYMBOLS}{message['text']}"
            else:
                next_append = False
                msgs.append({'username': username, 'message': message, 'avatar': avatar})
                if 'photo' in message:
                    next_append = True

        return msgs
