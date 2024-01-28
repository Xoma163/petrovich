from apps.bot.api.meme_arsenal import MemeArsenal as MemeArsenalAPI
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage


class MemeArsenal(Command):
    name = "мемарсенал"
    names = ["арсенал"]

    help_text = HelpText(
        commands_text="ищет мемы по названию",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("(текст)", "ищет мемы по названию и присылает топ-5")
            ])
        ]
    )

    args = 1

    def start(self) -> ResponseMessage:
        ma_api = MemeArsenalAPI()
        memes = ma_api.get_memes(self.event.message.args_str)
        if not memes:
            raise PWarning("Не нашёл :(")
        attachments = [self.bot.get_photo_attachment(x['url']) for x in memes]
        text_list = []
        for i, meme in enumerate(memes):
            text_list.append(f"{i + 1}. {meme['title']}")
        text = "\n".join(text_list)

        answer = f"Результаты по запросу '{self.event.message.args_str}'\n\n{text}"
        return ResponseMessage(ResponseMessageItem(text=answer, attachments=attachments))
