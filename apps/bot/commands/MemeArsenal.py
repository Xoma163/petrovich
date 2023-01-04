from apps.bot.APIs.MemeArsenalAPI import MemeArsenalAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Exceptions import PWarning


class MemeArsenal(Command):
    name = "мемарсенал"
    names = ["арсенал"]

    help_text = "ищет мемы по названию"
    help_texts = [
        "(текст) - ищет мемы по названию и присылает топ-5"
    ]

    def start(self):
        ma_api = MemeArsenalAPI()
        memes = ma_api.get_memes(self.event.message.args_str)
        if not memes:
            raise PWarning("Не нашёл :(")
        attachments = self.bot.upload_photos([x['url'] for x in memes], guarantee_url=True)
        text_list = []
        for i, meme in enumerate(memes):
            text_list.append(f"{i + 1}. {meme['title']}")
        text = "\n".join(text_list)

        return {'text': f"Результаты по запросу '{self.event.message.args_str}\n\n{text}'", 'attachments': attachments}
