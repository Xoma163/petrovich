import json
import random
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse

from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile, Bot
from apps.bot.utils.quotes_generator import QuotesGenerator
from apps.bot.utils.utils import get_urls_from_text


class Nostalgia(Command):
    name = "ностальгия"

    help_text = HelpText(
        commands_text="генерирует картинку с сообщениями из конфы беседки мразей",
        help_texts=[
            HelpTextItem(Role.MRAZ, [
                HelpTextItemCommand(None, "присылает 10 случайных сообщений"),
                HelpTextItemCommand("(N,M=10)",
                                    "присылает сообщения с позиции N до M. Максимальная разница между N и M - 200"),
                HelpTextItemCommand("(вложения)", "присылает вложения со скриншота"),
                HelpTextItemCommand("(фраза)", "ищет фразу по переписке"),
                HelpTextItemCommand("поиск (фраза) [N=1]", "ищет фразу по переписке. N - номер страницы")
            ])
        ]
    )

    access = Role.MRAZ

    platforms = [Platform.TG]

    bot: TgBot

    DEFAULT_MSGS_COUNT = 10

    KEY = "mrazi"
    FILE = "secrets/mrazi_chats/mrazi_all.json"
    MAX_PER_PAGE = 10

    def check_rights(self):
        if not (self.event.is_from_pm or self.event.chat and self.event.chat.pk == 56):
            raise PWarning("Команда работает только в ЛС или конфе мразей")

    def start(self) -> ResponseMessage:
        self.check_rights()
        if self.event.message.args:
            arg0 = str(self.event.message.args[0])
        else:
            arg0 = None

        if self.event.message.args:
            if len(self.event.message.args) == 2:
                self.int_args = [0, 1]
                try:
                    self.parse_int()
                    rmi = self.menu_range(self.event.message.args[0], self.event.message.args[1])
                    return rmi
                except PWarning:
                    pass
            else:
                self.int_args = [0]
                try:
                    self.parse_int()
                    rmi = self.menu_range(self.event.message.args[0])
                    return rmi
                except PWarning:
                    pass

        menu = [
            [['в', 'вложения'], self.menu_attachments],
            [['поиск'], self.menu_search],
            [['default'], self.menu_default]
        ]
        rm = self.handle_menu(menu, arg0)()
        return rm

    def menu_attachments(self) -> ResponseMessage:
        data = self._load_file()
        self.check_args(3)
        self.int_args = [1, 2]
        self.parse_int()
        index_from, index_to = self.event.message.args[1:3]
        msgs = data[index_from - 1: index_to]
        all_urls = []
        for msg in msgs:
            for att in msg['attachments']:
                if 'link' in att:
                    all_urls.append(att['link'])
                all_urls += get_urls_from_text(msg['text'])
        atts = []
        texts = []
        for url in all_urls:
            att = None
            ext = urlparse(url).path.rsplit('.')[-1]
            if ext in ["jpg", "png", "jpeg"]:
                link_name = "Фото"
                att = self.bot.get_photo_attachment(url)
            elif ext in ["gif", "gifv"]:
                link_name = "Гиф"
                att = self.bot.get_gif_attachment(url)
            elif "youtu.be" in url or "youtube" in url:
                link_name = "Ютуб"
            elif "vk.com/video" in url:
                link_name = "Вк видео"
            elif "vk.com/doc" in url:
                link_name = "Вк документ"
            elif "vk.com/im" in url and "photo" in url:
                link_name = "Вк фото"
            else:
                link_name = "Ссылка"
            text = self.bot.get_formatted_url(link_name, url)
            texts.append(text)
            if att:
                atts.append(att)
        if not texts:
            raise PWarning("Нет вложений")
        answer = "\n".join(texts)
        return ResponseMessage([
            ResponseMessageItem(attachments=atts),
            ResponseMessageItem(text=answer, disable_web_page_preview=True),
        ])

    def menu_default(self) -> ResponseMessage:
        if self.event.message.args:
            return self.menu_search()
        return self.menu_range()

    def menu_search(self) -> ResponseMessage:

        data = self._load_file()

        try:
            page = int(self.event.message.args[-1])
            if page < 1:
                page = 1
            search_list = self.event.message.raw.split(' ')[1:-1]
        except ValueError:
            page = 1
            search_list = self.event.message.raw.split(' ')[1:]

        search_query = " ".join(search_list)

        search_list = list(map(lambda x: x.lower(), search_list))
        searched_indexes = []
        for i, item in enumerate(data):
            if all(y in item['text'].lower() for y in search_list):
                searched_indexes.append(i)
        if len(searched_indexes) == 0:
            answer = f"Ничего не нашёл по запросу \"{search_query}\""
            return ResponseMessage(ResponseMessageItem(text=answer))
        total_pages = (len(searched_indexes) - 1) // self.MAX_PER_PAGE + 1
        if page * self.MAX_PER_PAGE > len(searched_indexes):
            page = total_pages
        first_item = (page - 1) * self.MAX_PER_PAGE
        last_item = min((page * self.MAX_PER_PAGE, len(searched_indexes)))
        buttons = []
        for i in range(first_item, last_item):
            index = searched_indexes[i]
            author = data[index]['author'].split(' ')[0]
            button = self.bot.get_button(f"{author}: {data[index]['text']}", self.name, [index + 1], )
            buttons.append(button)
        keyboard = self.bot.get_inline_keyboard(buttons)
        answer = f"Результаты по запросу \"{search_query}\".\n\nСтраница {page}/{total_pages}"
        return ResponseMessage(ResponseMessageItem(text=answer, keyboard=keyboard))

    def menu_range(self, index_from: int = None, index_to: int = None) -> ResponseMessage:
        data = self._load_file()

        if index_from is None:
            index_from = random.randint(0, len(data) - self.DEFAULT_MSGS_COUNT)

        index_from = max(index_from, 1)

        if index_to is None:
            index_to = index_from + self.DEFAULT_MSGS_COUNT

        if index_from > index_to:
            index_from, index_to = index_to, index_from
            index_from = max(index_from, 1)

        if index_to - index_from > 200:
            raise PWarning("Ну давай не надо больше 200 сообщений... Проц перегреется")

        if index_to > len(data):
            diff = index_to - index_from
            index_to = len(data) - 1
            index_from = index_to - diff

        msgs = data[index_from - 1:index_to]
        msgs_parsed, has_att_link = self.prepare_msgs_for_quote_generator(msgs)

        qg = QuotesGenerator()
        pil_image = qg.build(msgs_parsed, title="Ностальгия")
        bytes_io = BytesIO()
        pil_image.save(bytes_io, format='PNG')
        if pil_image.height > 1500:
            image = self.bot.get_document_attachment(bytes_io, self.event.peer_id, filename="petrovich_nostalgia.png")
        else:
            image = self.bot.get_photo_attachment(bytes_io, peer_id=self.event.peer_id,
                                                  filename="petrovich_nostalgia.png")
        answer = f"{msgs[0]['datetime']}\n" \
                 f"{index_from} - {index_to}"
        button = self.bot.get_button("Ещё", self.name)
        buttons = [button]
        diff = index_to - index_from + 1
        if index_from != 1:
            button = self.bot.get_button("До", self.name, [index_from - diff, index_to - diff])
            buttons.append(button)
        if index_to != len(data) - 1:
            button = self.bot.get_button("После", self.name, [index_from + diff, index_to + diff])
            buttons.append(button)
        if has_att_link:
            button = self.bot.get_button("Вложения", self.name, ["в", index_from, index_to])
            buttons.append(button)

        keyboard = self.bot.get_inline_keyboard(buttons)

        return ResponseMessage(ResponseMessageItem(text=answer, attachments=[image], keyboard=keyboard))

    def _load_file(self) -> list:
        with open(self.FILE, 'r') as file:
            content = json.loads(file.read())
        return content

    def merge_files(self, *files):
        dt_format = "%d.%m.%Y %H:%M:%S"
        result_file = []
        counters = [0] * len(files)
        lens = [len(x) for x in files]
        for _ in range(sum(lens)):
            early_date = None
            early_counter_index = 0
            for i, counter in enumerate(counters):
                if counter >= lens[early_counter_index]:
                    counters[early_counter_index] -= 1
                date = datetime.strptime(files[i][counters[i]]['datetime'], dt_format)
                if not early_date or date < early_date:
                    early_date = date
                    early_counter_index = i
            counter = counters[early_counter_index]
            result_file.append(files[early_counter_index][counter])
            counters[early_counter_index] += 1

        with open(self.FILE, 'w') as file:
            file.write(json.dumps(result_file, ensure_ascii=False, indent=2))
        return result_file

    @staticmethod
    def prepare_msgs_for_quote_generator(msgs):
        has_att_link = False
        new_msgs = []
        users_avatars = {}
        for msg in msgs:
            message = {'text': msg['text']}
            if get_urls_from_text(msg['text']):
                has_att_link = True
            for att in msg['attachments']:
                if att['type'] == "Фотография":
                    message['photo'] = att['link']
                    has_att_link = True
                elif att['type'] in ["Видеозапись", "Файл", "Ссылка", "Голосовое сообщение"]:
                    message['text'] += f'\n{att["link"]}'
                    has_att_link = True
                message['text'] += f"\n({att['type']})\n"
            if msg['fwd']:
                message['text'] += '\n(Пересланные сообщения)\n'
            message['text'] = message['text'].strip()
            if msg['author'] not in users_avatars:
                try:
                    name, surname = msg['author'].split(' ', 1)
                    if name == "Игорь" and surname == "Петрович":
                        user = Bot.objects.filter(name=msg['author']).first()
                    else:
                        user = Profile.objects.filter(name=name, surname=surname).first()
                except Exception:
                    user = None
                if user:
                    users_avatars[msg['author']] = user.avatar
            avatar = users_avatars.get(msg['author'], None)

            new_msg = {'username': msg['author'], 'message': message, 'avatar': avatar}
            new_msgs.append(new_msg)
        return new_msgs, has_att_link
