import json
import random
from io import BytesIO

from apps.bot.classes.Consts import Platform, Role
from apps.bot.classes.Exceptions import PWarning
from apps.bot.classes.QuotesGenerator import QuotesGenerator
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.bot.models import Users
from apps.service.models import Service


class Nostalgia(CommonCommand):
    name = "ностальгия"
    names = ["ностальжи", "(с)"]
    help_text = "генерирует картинку с сообщениями из конфы беседки мразей"
    help_texts = [
        "- присылает 10 случайных сообщений",
        "(N,M=10) - присылает сообщения с позиции N до M. Максимальная разница между N и M - 200",
        "(до) - присылает несколько сообщений до",
        "(после) - присылает несколыько сообщений после",
        "(вложения) - присылает вложения со скриншота"
    ]
    access = Role.MRAZ

    DEFAULT_MSGS_COUNT = 10

    def start(self):
        if self.event.args:
            arg0 = self.event.args[0].lower()
        else:
            arg0 = None

        if self.event.args:
            if len(self.event.args) == 2:
                self.int_args = [0, 1]
                try:
                    self.parse_int()
                    return self.menu_range(self.event.args[0], self.event.args[1])
                except PWarning:
                    pass
            else:
                self.int_args = [0]
                try:
                    self.parse_int()
                    return self.menu_range(self.event.args[0])
                except PWarning:
                    pass

        menu = [
            [["до"], self.menu_before],
            [["после"], self.menu_after],
            [['вложения'], self.menu_attachments],
            [['default'], self.menu_range]
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
        return "\n".join(all_atts)

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
            attachments = self.bot.upload_photos(bytes_io)
        msg = f"{msgs[0]['datetime']}\n" \
              f"{index_from} - {index_to}"
        buttons = [{'command': self.name, 'button_text': "Ещё", 'args': None}]
        if index_from != 1:
            buttons.append({'command': self.name, 'button_text': "До", 'args': "до"})
        if index_to != len(data) - 1:
            buttons.append({'command': self.name, 'button_text': "После", 'args': "после"})
        if has_att_link:
            buttons.append({'command': self.name, 'button_text': "Вложения", 'args': "вложения"})

        keyboard = self.bot.get_inline_keyboard(buttons)

        return {"msg": msg, "attachments": attachments, "keyboard": keyboard}

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
            for att in msg['attachments']:
                if att['type'] == "Фотография":
                    message['photo'] = att['link']
                    has_att_link = True
                elif att['type'] in ["Видеозапись", "Файл", "Ссылка"]:
                    message['text'] += f'\n{att["link"]}'
                    has_att_link = True
                else:
                    message['text'] += f"{att['type']}\n"
                if msg['fwd']:
                    message['text'] += '\n(Пересланные сообщения)\n'

            if msg['author'] not in users_avatars:
                name, surname = msg['author'].split(' ', 1)
                vk_user = Users.objects.filter(name=name, surname=surname, platform=Platform.VK.name).first()
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
