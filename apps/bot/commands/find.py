from apps.bot.api.google_custom_search import GoogleCustomSearch
from apps.bot.classes.bots.chat_activity import ChatActivity
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpTextItem, HelpText, HelpTextArgument
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem


class Find(Command):
    name = "найди"
    names = ["поиск", "найти", "ищи", "искать", "хуизфакинг", "вхуизфакинг"]
    help_text = HelpText(
        commands_text="ищет информацию по картинкам в гугле",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextArgument("(запрос)", "присылает картинки по поиску в гугле"),
                HelpTextArgument("(пересланное сообщение)", "присылает картинки по поиску в гугле")
            ])
        ]
    )

    args_or_fwd = True
    platforms = [Platform.TG]

    bot: TgBot

    def start(self) -> ResponseMessage:
        if self.event.message.args:
            query = self.event.message.args_str
        elif self.event.message.quote:
            query = self.event.message.quote
        elif self.event.fwd:
            query = self.event.fwd[0].message.raw
        else:
            raise PWarning("В сообщении должны быть аргументы или пересылаемое сообщение")

        count = 5

        gcs_api = GoogleCustomSearch(log_filter=self.event.log_filter)
        urls = gcs_api.get_images_urls(query)
        if len(urls) == 0:
            raise PWarning("Ничего не нашёл по картинкам")

        attachments = []
        with ChatActivity(self.bot, ActivitiesEnum.UPLOAD_PHOTO, self.event.peer_id):
            for url in urls:
                try:
                    att = PhotoAttachment()
                    att.public_download_url = url
                    att.set_file_id()
                    attachments.append(att)
                except Exception:
                    continue
                if len(attachments) == count:
                    break
        if len(attachments) == 0:
            raise PWarning("Ничего не нашёл по картинкам")
        answer = f"Результаты по запросу '{query}'"
        return ResponseMessage(ResponseMessageItem(text=answer, attachments=attachments))
