import wikipedia

from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.bots.VkBot import VkBot
from apps.bot.classes.common.CommonCommand import CommonCommand

wikipedia.set_lang("ru")


class Wikipedia(CommonCommand):
    names = ["вики", "википедия"]
    help_text = "Вики - поиск информации в википедии"
    detail_help_text = "Вики (фраза) - поиск информации в википедии\n" \
                       "Вики р - рандомная статья в википедии"
    args = 1

    def start(self):
        self.bot.set_activity(self.event.peer_id)

        is_random = False
        if self.event.args[0].lower() in ["рандом", "р"]:
            is_random = True
            search_query = wikipedia.random()
        else:
            search_query = self.event.original_args
        try:
            page = wikipedia.page(search_query)
            if page.summary != '':
                msg = f"{page.original_title}\n\n{page.summary}\n\nПодробнее: {page.url}"
            else:
                msg = f"{page.original_title}\n\n{page.content}\n\nПодробнее: {page.url}"
            output = {'msg': msg, 'attachments': [page.url]}
            if page.images:
                attachments = self.bot.upload_photos(page.images, 3)
                if isinstance(self.bot, VkBot):
                    output['attachments'] += attachments
                else:
                    if len(attachments) > 1:
                        self.bot.parse_and_send_msgs(self.event.peer_id, {'msg': msg, 'attachments': attachments})
            if is_random:
                output['keyboard'] = self.bot.get_inline_keyboard(self.names[0], args={"random": "р"})
            return output
        except wikipedia.DisambiguationError as e:
            options = set(e.options)
            msg = "Нашел сразу несколько. Уточните\n"
            msg += "\n".join([x for x in options])
            raise PWarning(msg)
        except wikipedia.PageError:
            msg = "Не нашёл такой страницы\n"
            search = wikipedia.search(self.event.original_args)
            if len(search) == 0:
                msg += "Результат поиска ничего не дал"
            else:
                msg += "Я нашел возможные варианты:\n"
                search = list(map(lambda x: f"- {x}", search))
                msg += "\n".join(search)
            return msg

# Если он серит в консоль, то
#  lib/wikipedia/wikipedia.py:389
#  lis = BeautifulSoup(html, 'html.parser').find_all('li')
