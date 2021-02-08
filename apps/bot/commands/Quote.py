import datetime

from apps.bot.classes.Consts import Platform
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import QuoteBook


# ToDo: Deprecated
class Quote(CommonCommand):
    names = ["цитата", "(c)", "(с)"]
    help_text = "Цитата - сохраняет в цитатник сообщения"
    detail_help_text = "Цитата (Пересылаемые сообщение) - сохраняет в цитатник сообщения"
    fwd = True
    platforms = [Platform.VK, Platform.TG]
    enabled = False

    def start(self):
        msgs = self.event.fwd

        quote = QuoteBook()
        quote_text = ""
        for msg in msgs:
            text = msg['text']
            if msg['from_id'] > 0:
                quote_user_id = int(msg['from_id'])
                quote_user = self.bot.get_user_by_id(quote_user_id)
                username = str(quote_user)
            else:
                quote_bot_id = int(msgs[0]['from_id'])
                quote_bot = self.bot.get_bot_by_id(quote_bot_id)
                username = str(quote_bot)
            quote_text += f"{username}:\n{text}\n\n"
        quote.text = quote_text
        if self.event.chat:
            quote.chat = self.event.chat
        else:
            quote.user = self.event.sender
        quote.date = datetime.datetime.utcnow()
        quote.save()
        return "Цитата сохранена"
