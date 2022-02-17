import json
import random
from io import BytesIO

from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Role
from apps.bot.classes.consts.Exceptions import PWarning
from apps.bot.models import Profile
from apps.bot.utils.QuotesGenerator import QuotesGenerator
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
        "(вложения) - присылает вложения со скриншота"
        "(фраза) - ищет фразу по переписке"
        "поиск (фраза) [N=1] - ищет фразу по переписке. N - номер страницы"
    ]
    access = Role.MRAZ

    DEFAULT_MSGS_COUNT = 10

    def start(self):
        if self.event.message.args:
            arg0 = str(self.event.message.args[0])
        else:
            arg0 = None

        if self.event.message.args:
            if len(self.event.message.args) == 2:
                self.int_args = [0, 1]
                try:
                    self.parse_int()
                    return self.menu_range(self.event.message.args[0], self.event.message.args[1])
                except PWarning:
                    pass
            else:
                self.int_args = [0]
                try:
                    self.parse_int()
                    return self.menu_range(self.event.message.args[0])
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

    def menu_before(self):
        index_from, index_to = self._get_indexes_from_db()
        diff = index_to - index_from + 1
        return self.menu_range(index_to - diff, index_from - diff)

    def menu_after(self):
        index_from, index_to = self._get_indexes_from_db()
        diff = index_to - index_from + 1
        return self.menu_range(index_to + diff, index_from + diff)

    def menu_attachments(self):
        data = self._load_file()
        index_from, index_to = self._get_indexes_from_db()
        msgs = data[index_from - 1: index_to]
        all_atts = []
        for msg in msgs:
            for att in msg['attachments']:
                if 'link' in att:
                    all_atts.append(att['link'])
            all_atts += get_urls_from_text(msg['text'])

        return "\n".join(all_atts)

    def menu_default(self):
        if self.event.message.args:
            return self.menu_search()
        return self.menu_range()

    def menu_search(self):
        MAX_PER_PAGE = 10
        data = self._load_file()

        try:
            page = int(self.event.message.args[-1])
            if page < 1:
                page = 1
            search_list = self.event.message.args[:-1]
        except ValueError:
            page = 1
            search_list = self.event.message.args

        search_query = " ".join(search_list)

        search_list = list(map(lambda x: x.lower(), search_list))
        searched_indexes = []
        for i, item in enumerate(data):
            if all(y in item['text'].lower() for y in search_list):
                searched_indexes.append(i)
        if len(searched_indexes) == 0:
            return f'Ничего не нашёл по запросу "{search_query}"'
        total_pages = (len(searched_indexes) - 1) // MAX_PER_PAGE + 1
        if page * MAX_PER_PAGE > len(searched_indexes):
            page = total_pages
        first_item = (page - 1) * MAX_PER_PAGE
        last_item = min((page * MAX_PER_PAGE, len(searched_indexes)))
        buttons = []
        for i in range(first_item, last_item):
            index = searched_indexes[i]
            author = data[index]['author'].split(' ')[0]
            buttons.append(
                {'command': self.name, 'button_text': f"{author}: {data[index]['text']}", 'args': [index + 1]})

        keyboard = self.bot.get_inline_keyboard(buttons)

        return {"text": f"Результаты по запросу {search_query}.\n\nСтраница {page}/{total_pages}", "keyboard": keyboard}

    def menu_range(self, index_from: int = None, index_to: int = None):
        data = self._load_file()

        if index_from is None:
            index_from = random.randint(0, len(data) - self.DEFAULT_MSGS_COUNT)

        if index_from < 1:
            index_from = 1

        if index_to is None:
            index_to = index_from + self.DEFAULT_MSGS_COUNT

        if index_from > index_to:
            index_from, index_to = index_to, index_from
            if index_from < 1:
                index_from = 1

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
            attachments = self.bot.upload_document(bytes_io, self.event.peer_id, "Ностальгия", filename="nostalgia.png")
        else:
            attachments = self.bot.upload_photos(bytes_io, peer_id=self.event.peer_id)
        msg = f"{msgs[0]['datetime']}\n" \
              f"{index_from} - {index_to}"
        buttons = [{'command': self.name, 'button_text': "Ещё", 'args': None}]
        diff = index_to - index_from + 1
        if index_from != 1:
            buttons.append({'command': self.name, 'button_text': "До", 'args': [index_from - diff, index_to - diff]})
        if index_to != len(data) - 1:
            buttons.append({'command': self.name, 'button_text': "После", 'args': [index_from + diff, index_to + diff]})
        if has_att_link:
            buttons.append({'command': self.name, 'button_text': "Вложения", 'args': "вложения"})

        keyboard = self.bot.get_inline_keyboard(buttons)

        return {"text": msg, "attachments": attachments, "keyboard": keyboard}

    @staticmethod
    def _load_file() -> list:
        with open('secrets/mrazi_chats/mrazi1.json', 'r') as file:
            content = file.read()
        return json.loads(content)

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
                name, surname = msg['author'].split(' ', 1)
                vk_user = Profile.objects.filter(name=name, surname=surname).first()
                if vk_user:
                    users_avatars[msg['author']] = vk_user.avatar
            avatar = users_avatars.get(msg['author'], None)

            new_msg = {'username': msg['author'], 'message': message, 'avatar': avatar}
            new_msgs.append(new_msg)
        return new_msgs, has_att_link

    @staticmethod
    def _get_indexes_from_db():
        index_from, _ = Service.objects.get_or_create(name='mrazi_chats_index_from')
        index_to, _ = Service.objects.get_or_create(name='mrazi_chats_index_to')
        return int(index_from.value), int(index_to.value)

    @staticmethod
    def _set_indexes_to_db(index_from, index_to):
        index_from_obj = Service.objects.get(name='mrazi_chats_index_from')
        index_from_obj.value = index_from
        index_from_obj.save()

        index_to_obj = Service.objects.get(name='mrazi_chats_index_to')
        index_to_obj.value = index_to
        index_to_obj.save()
