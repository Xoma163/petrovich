import json
import random
from datetime import datetime
from io import BytesIO

from apps.bot.classes.bots.tg import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.consts import Role, Platform
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.models import Profile, Bot
from apps.bot.utils.quotes_generator import QuotesGenerator
from apps.bot.utils.utils import get_urls_from_text
from apps.service.models import Service


class Nostalgia(Command):
    name = "ностальгия"
    help_text = "генерирует картинку с сообщениями из конфы беседки мразей"
    help_texts = [
        "- присылает 10 случайных сообщений",
        "(N,M=10) - присылает сообщения с позиции N до M. Максимальная разница между N и M - 200",
        "(до) - присылает несколько сообщений до",
        "(после) - присылает несколыько сообщений после",
        "(вложения) - присылает вложения со скриншота",
        "(фраза) - ищет фразу по переписке",
        "поиск (фраза) [N=1] - ищет фразу по переписке. N - номер страницы"
    ]
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
                    return ResponseMessage(rmi)
                except PWarning:
                    pass
            else:
                self.int_args = [0]
                try:
                    self.parse_int()
                    rmi = self.menu_range(self.event.message.args[0])
                    return ResponseMessage(rmi)
                except PWarning:
                    pass

        menu = [
            [["до"], self.menu_before],
            [["после"], self.menu_after],
            [['вложения'], self.menu_attachments],
            [['поиск'], self.menu_search],
            [['default'], self.menu_default]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def menu_before(self) -> ResponseMessageItem:
        index_from, index_to = self._get_indexes_from_db()
        diff = index_to - index_from + 1
        return self.menu_range(index_to - diff, index_from - diff)

    def menu_after(self) -> ResponseMessageItem:
        index_from, index_to = self._get_indexes_from_db()
        diff = index_to - index_from + 1
        return self.menu_range(index_to + diff, index_from + diff)

    def menu_attachments(self) -> ResponseMessageItem:
        data = self._load_file()
        index_from, index_to = self._get_indexes_from_db()
        msgs = data[index_from - 1: index_to]
        all_atts = []
        for msg in msgs:
            for att in msg['attachments']:
                if 'link' in att:
                    all_atts.append(self.bot.get_formatted_url("Ссылка", att['link']))
            all_atts += get_urls_from_text(msg['text'])
        answer = "\n".join(all_atts)
        return ResponseMessageItem(text=answer)

    def menu_default(self) -> ResponseMessageItem:
        if self.event.message.args:
            return self.menu_search()
        return self.menu_range()

    def menu_search(self) -> ResponseMessageItem:

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
            answer = f'Ничего не нашёл по запросу "{search_query}"'
            return ResponseMessageItem(text=answer)
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
        answer = f"Результаты по запросу {search_query}.\n\nСтраница {page}/{total_pages}"
        return ResponseMessageItem(text=answer, keyboard=keyboard)

    def menu_range(self, index_from: int = None, index_to: int = None) -> ResponseMessageItem:
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

        self._set_indexes_to_db(index_from, index_to)

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
            button = self.bot.get_button("Вложения", self.name, ["вложения"])
            buttons.append(button)

        keyboard = self.bot.get_inline_keyboard(buttons)

        return ResponseMessageItem(text=answer, attachments=[image], keyboard=keyboard)

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
                if not early_date:
                    early_date = date
                    early_counter_index = i
                elif date < early_date:
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
                except:
                    user = None
                if user:
                    users_avatars[msg['author']] = user.avatar
            avatar = users_avatars.get(msg['author'], None)

            new_msg = {'username': msg['author'], 'message': message, 'avatar': avatar}
            new_msgs.append(new_msg)
        return new_msgs, has_att_link

    def _get_indexes_from_db(self):
        index_from, _ = Service.objects.get_or_create(name=f'{self.KEY}_chats_index_from')
        index_to, _ = Service.objects.get_or_create(name=f'{self.KEY}_chats_index_to')
        return int(index_from.value), int(index_to.value)

    def _set_indexes_to_db(self, index_from, index_to):
        index_from_obj, _ = Service.objects.get_or_create(name=f'{self.KEY}_chats_index_from')
        index_from_obj.value = index_from
        index_from_obj.save()

        index_to_obj, _ = Service.objects.get_or_create(name=f'{self.KEY}_chats_index_to')
        index_to_obj.value = index_to
        index_to_obj.save()
