import wikipedia

from apps.bot.classes.Command import Command
from apps.bot.classes.bots.VkBot import VkBot
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Exceptions import PWarning

wikipedia.set_lang("ru")


class Wikipedia(Command):
    name = "вики"
    names = ["википедия"]
    help_text = "поиск информации в википедии"
    help_texts = [
        "(фраза) - поиск информации в википедии",
        "р - рандомная статья в википедии"
    ]
    args = 1

    def start(self):
        self.bot.set_activity(self.event.peer_id, ActivitiesEnum.TYPING)

        is_random = False
        if self.event.message.args[0].lower() in ["рандом", "р"]:
            is_random = True
            search_query = wikipedia.random()
        else:
            search_query = self.event.message.args_str
        try:
            page = wikipedia.page(search_query)
            if page.summary != '':
                text = f"{page.original_title}\n\n{page.summary}\n\nПодробнее: {page.url}"
            else:
                text = f"{page.original_title}\n\n{page.content}\n\nПодробнее: {page.url}"
            output = {'text': text, 'attachments': [page.url]}
            if page.images:
                attachments = self.bot.upload_photos(page.images, 3)
                if isinstance(self.bot, VkBot):
                    output['attachments'] += attachments
                else:
                    if len(attachments) > 1:
                        self.bot.parse_and_send_msgs(self.event.peer_id, {'text': text, 'attachments': attachments})
            if is_random:
                output['keyboard'] = self.bot.get_inline_keyboard(
                    [{'command': self.name, 'button_text': "Ещё", 'args': ['р']}])
            return output
        except wikipedia.DisambiguationError as e:
            options = set(e.options)
            text = "Нашел сразу несколько. Уточните\n"
            text += "\n".join([x for x in options])
            raise PWarning(text)
        except wikipedia.PageError:
            text = "Не нашёл такой страницы\n"
            search = wikipedia.search(self.event.message.args_str)
            if len(search) == 0:
                text += "Результат поиска ничего не дал"
            else:
                text += "Я нашел возможные варианты:\n"
                search = list(map(lambda x: f"- {x}", search))
                text += "\n".join(search)
            return text

# Если он серит в консоль, то
#  lib/wikipedia/wikipedia.py:389
#  lis = BeautifulSoup(html, 'html.parser').find_all('li')
