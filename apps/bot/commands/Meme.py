from urllib.parse import urlparse

from apps.bot.classes.Command import Command
from apps.bot.classes.bots.Bot import get_moderator_bot_class, upload_image_to_vk_server
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PSkip, PWarning, PError
from apps.bot.utils.utils import get_attachments_from_attachments_or_fwd, tanimoto
from apps.service.models import Meme as MemeModel
from petrovich.settings import VK_URL
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.AudioAttachment import AudioAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment


def check_name_exists(name):
    return MemeModel.objects.filter(name=name).exists()


# noinspection PyUnresolvedReferences,PyUnresolvedReferences
class Meme(Command):
    name = "мем"
    help_text = "присылает нужный мем"
    help_texts = [
        "(название) - присылает нужный мем. Можно использовать * вместо символов поиска. Например /мем ж*па",
        "р - присылает рандомный мем",
        "добавить (название) (Вложение/Пересланное сообщение с вложением) - добавляет мем. ",
        "добавить (ссылка на youtube/coub) (название) - добавляет мем с youtube/coub. ",
        "обновить (название) (Вложение/Пересланное сообщение с вложением) - обновляет созданный вами мем. Можно добавлять картинки/аудио/видео",
        "обновить (название) (ссылка на youtube/coub) - обновляет созданный вами мем.",
        "удалить (название) - удаляет созданный вами мем",
        "конфа (название конфы) (название/рандом) - отправляет мем в конфу\n",

        "подтвердить - присылает мем на подтверждение (для модераторов)",
        "подтвердить (id/название) [новое название] - подтверждает мем (для модераторов)",
        "отклонить (id) [причина] - отклоняет мем (для модераторов)",
        "переименовать (id) (новое название) - переименовывает мем (для модераторов)",
        "удалить (id/название) [причина] - удаляет мем (для модераторов)",
        "инфо (id/название) - присылает информацию по мему (для модераторов)"
    ]
    args = 1
    platforms = [Platform.VK, Platform.TG]
    priority = 70

    def accept(self, event):
        if event.chat and event.message and check_name_exists(event.message.clear.lower()):
            if not event.chat.need_meme:
                raise PSkip()
            event.message.args = event.message.clear.lower().split(' ')
            return True
        return super().accept(event)

    def start(self):
        arg0 = self.event.message.args[0].lower()
        menu = [
            [['добавить'], self.menu_add],
            [['обновить'], self.menu_refresh],
            [['удалить'], self.menu_delete],
            [['рандом', 'р'], self.menu_random],
            [['подтвердить', 'принять', '+'], self.menu_confirm],
            [['отклонить', 'отменить', '-'], self.menu_reject],
            [['переименовать', 'правка'], self.menu_rename],
            [['id', 'ид'], self.menu_id],
            [['инфо'], self.menu_info],
            [['default'], self.menu_default]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    @staticmethod
    def _check_allowed_url(url):
        parsed_url = urlparse(url)
        if not parsed_url.hostname:
            raise PWarning("Не нашёл вложений в сообщении или пересланном сообщении. Не нашёл ссылку на youtube видео")

        if parsed_url.hostname.replace('www.', '').lower() not in ['youtu.be', 'youtube.com', 'coub.com']:
            raise PWarning("Это ссылка не на youtube/coub видео")

    # MENU #

    def menu_add(self):
        self.check_args(2)
        attachments = get_attachments_from_attachments_or_fwd(self.event, [AudioAttachment, VideoAttachment, PhotoAttachment])
        if len(attachments) == 0:
            url = self.event.message.args_str.split(' ')[1]
            self._check_allowed_url(url)

            attachment = {
                'type': 'link',
                'url': url,
            }
            meme_name = " ".join(self.event.message.args[2:]).lower()
        else:
            meme_name = " ".join(self.event.message.args[1:]).lower()
            attachment = attachments[0]

        if self.event.platform != Platform.VK and attachment['type'] not in ['photo', 'link']:
            raise PWarning('В данной платформе поддерживается добавление только картинок-мемов и youtube/coub ссылок')

        for i, _ in enumerate(self.event.message.args):
            self.event.message.args[i] = self.event.message.args[i].lower()

        new_meme = {
            'name': meme_name,
            'type': attachment['type'],
            'author': self.event.sender,
            'approved': self.event.sender.check_role(Role.MODERATOR) or self.event.sender.check_role(Role.TRUSTED)
        }

        ban_list = ['добавить', 'обновить', 'удалить', 'конфа', 'рандом', 'р', 'подтвердить', 'принять', '+',
                    'отклонить', 'отменить', '-', 'переименовать', 'правка', 'id', 'ид', 'инфо']
        if new_meme['name'] in ban_list:
            raise PWarning("Мем с таким названием нельзя создать")

        if MemeModel.objects.filter(name=new_meme['name']).exists():
            raise PWarning("Мем с таким названием уже есть в базе")

        if attachment['type'] in ['video', 'audio', 'link']:
            new_meme['link'] = attachment['url']
        elif attachment['type'] == 'photo':  # or attachment['type'] == 'doc':
            if self.event.platform == Platform.VK:
                new_meme['link'] = attachment['download_url']
            else:
                new_meme['link'] = upload_image_to_vk_server(attachment['content'])
        else:
            raise PError("Невозможно")

        new_meme_obj = MemeModel.objects.create(**new_meme)
        if new_meme['approved']:
            return "Добавил"
        else:
            meme_to_send = self.prepare_meme_to_send(new_meme_obj)
            meme_to_send['text'] = "Запрос на подтверждение мема:\n" \
                                   f"{new_meme_obj.author}\n" \
                                   f"{new_meme_obj.name} ({new_meme_obj.id})"

            # Отправка сообщения в модераторную
            m_bot = get_moderator_bot_class()()
            m_bot.parse_and_send_msgs(self.bot.test_chat.chat_id, meme_to_send)
            return "Добавил. Воспользоваться мемом можно после проверки модераторами."

    def menu_refresh(self):
        self.check_args(2)
        _id = None
        if 2 <= len(self.event.message.args) <= 3:
            try:
                _id = int(self.event.message.args[1])
            except PWarning:
                pass
        meme_name = " ".join(self.event.message.args[1:]).lower()

        attachments = get_attachments_from_attachments_or_fwd(self.event, [AudioAttachment, VideoAttachment, PhotoAttachment])
        if len(attachments) == 0:
            if len(self.event.message.args) > 2:
                url = self.event.message.args[-1]
                try:
                    self._check_allowed_url(url)
                    attachments = [{'type': 'link', 'url': url}]
                    meme_name = self.event.message.args[1:-1]
                except Exception:
                    raise PWarning("Не нашёл вложений в сообщении или пересланном сообщении\n"
                                   "Не нашёл ссылки на youtube/coub")

        attachment = attachments[0]
        if attachment['type'] == 'video' or attachment['type'] == 'audio':
            new_meme_link = attachment['url']
        elif attachment['type'] == 'photo':  # or attachment['type'] == 'doc':
            if self.event.platform == Platform.VK:
                new_meme_link = attachment['download_url']
            else:
                new_meme_link = upload_image_to_vk_server(attachment['content'])

        elif attachment['type'] == 'link':
            new_meme_link = attachment['url']
        else:
            raise PError("Невозможно")

        if self.event.sender.check_role(Role.MODERATOR) or self.event.sender.check_role(Role.TRUSTED):
            meme = self.get_meme(meme_name, _id=_id)
            meme.link = new_meme_link
            meme.type = attachment['type']
            meme.save()
            return f'Обновил мем "{meme.name}"'
        else:
            meme = self.get_meme(meme_name, self.event.sender, _id=_id)
            meme.link = new_meme_link
            meme.approved = False
            meme.type = attachment['type']
            meme.save()

            meme_to_send = self.prepare_meme_to_send(meme)
            meme_to_send['text'] = "Запрос на обновление мема:\n" \
                                   f"{meme.author}\n" \
                                   f"{meme.name} ({meme.id})"
            self.bot.parse_and_send_msgs(self.bot.test_chat.chat_id, meme_to_send)
            return "Обновил. Воспользоваться мемом можно после проверки модераторами."

    def menu_delete(self):
        self.check_args(2)
        if self.event.sender.check_role(Role.MODERATOR):
            try:
                self.int_args = [1]
                self.parse_int()
                meme_id = self.event.message.args[1]
                meme = MemeModel.objects.filter(id=meme_id).first()
                reason = " ".join(self.event.message.args[2:])
                if reason:
                    msg = f'Мем с названием "{meme.name}" удалён. Причина: {reason}'
                else:
                    msg = f'Мем с названием "{meme.name}" удалён поскольку он не ' \
                          f'соответствует правилам или был удалён автором.'
            except PWarning:
                meme = self.get_meme(self.event.message.args[1:])
                msg = f'Мем с названием "{meme.name}" удалён поскольку он не ' \
                      f'соответствует правилам или был удалён автором.'
            if meme.author != self.event.sender:
                self.bot.send_message(meme.author.user_id, msg)
        else:
            meme = self.get_meme(self.event.message.args[1:], self.event.sender)
        meme_name = meme.name
        meme.delete()
        return f'Удалил мем "{meme_name}"'

    def menu_random(self):
        meme = self.get_random_meme()
        return self.prepare_meme_to_send(meme, print_name=True, send_keyboard=True)

    def menu_confirm(self):
        self.check_sender(Role.MODERATOR)
        if len(self.event.message.args) == 1:
            try:
                meme = self.get_meme(approved=False)
            except PWarning:
                raise PWarning("Не нашёл мемов для подтверждения")
            meme_to_send = self.prepare_meme_to_send(meme)
            meme_to_send['text'] = f"{meme.author}\n" \
                                   f"{meme.name} ({meme.id})"
            return meme_to_send
        else:
            self.int_args = [1]
            self.parse_int()
            non_approved_meme = self.get_meme(_id=self.event.message.args[1])

            if not non_approved_meme:
                raise PWarning("Не нашёл мема с таким id")
            if non_approved_meme.approved:
                raise PWarning("Мем уже подтверждён")
            if len(self.event.message.args) > 2:
                new_name = " ".join(self.event.message.args[2:])
                non_approved_meme.name = new_name

            user_msg = f'Мем с названием "{non_approved_meme.name}" подтверждён.'
            self.bot.send_message(non_approved_meme.author.user_id, user_msg)

            msg = f'Мем "{non_approved_meme.name}" ({non_approved_meme.id}) подтверждён'
            non_approved_meme.approved = True
            non_approved_meme.save()
            return msg

    def menu_reject(self):
        self.check_sender(Role.MODERATOR)
        self.check_args(2)
        self.int_args = [1]
        self.parse_int()
        non_approved_meme = self.get_meme(_id=self.event.message.args[1])
        if not non_approved_meme:
            raise PWarning("Не нашёл мема с таким id")
        if non_approved_meme.approved:
            raise PWarning("Мем уже подтверждён")

        reason = None
        if len(self.event.message.args) > 2:
            reason = " ".join(self.event.message.args[2:])
        user_msg = f'Мем с названием "{non_approved_meme.name}" отклонён.'
        if reason:
            user_msg += f"\nПричина: {reason}"
        self.bot.send_message(non_approved_meme.author.user_id, user_msg)

        msg = f'Мем "{non_approved_meme.name}" ({non_approved_meme.id}) отклонён'
        non_approved_meme.delete()
        return msg

    def menu_rename(self):
        self.check_sender(Role.MODERATOR)
        self.int_args = [1]
        self.parse_int()
        renamed_meme = self.get_meme(_id=self.event.message.args[1])
        if not renamed_meme:
            raise PWarning("Не нашёл мема с таким id")

        new_name = None
        if len(self.event.message.args) > 2:
            new_name = " ".join(self.event.message.args[2:])
        if MemeModel.objects.filter(name=new_name).exists():
            raise PWarning("Мем с таким названием уже есть")
        user_msg = f'Мем с названием "{renamed_meme.name}" переименован.\n' \
                   f'Новое название - "{new_name}"'
        if renamed_meme.author != self.event.sender:
            self.bot.send_message(renamed_meme.author.user_id, user_msg)
        renamed_meme.name = new_name
        renamed_meme.save()
        return user_msg

    def menu_id(self):
        self.check_args(2)
        self.int_args = [1]
        self.parse_int()
        _id = self.event.message.args[1]
        meme = self.get_meme(_id=_id)
        return self.prepare_meme_to_send(meme, True)

    def menu_info(self):
        self.check_args(2)
        _id = None
        if len(self.event.message.args) == 2:
            self.int_args = [1]
            try:
                self.parse_int()
                _id = self.event.message.args[1]
            except PWarning:
                pass
        meme = self.get_meme(self.event.message.args[1:], _id=_id)
        return meme.get_info()

    def menu_default(self):
        memes = self.get_meme(self.event.message.args, use_tanimoto=True)
        if isinstance(memes, list):
            meme = memes[0]
        else:
            meme = memes
        meme.uses += 1
        meme.save()
        prepared_meme = self.prepare_meme_to_send(meme)
        if isinstance(memes, MemeModel):
            return prepared_meme
        else:
            msg = self.get_similar_memes_names(memes)
            return [prepared_meme, msg]

    # END MENU #

    def get_meme(self, filter_list=None, filter_user=None, approved=True, _id=None, use_tanimoto=False):
        """
        :return: 1 мем. Если передан параметр use_tanimoto, то список мемов отсортированных по коэфф. Танимото
        """
        flag_regex = False
        memes = MemeModel.objects
        if _id:
            memes = memes.filter(id=_id)
        else:
            if filter_list is None:
                filter_list = []
            memes = memes.filter(approved=approved)
            if self.event.platform == Platform.TG:
                memes = memes.exclude(type='audio')
            if filter_list:
                filter_list = list(map(lambda x: x.lower(), filter_list))
                for _filter in filter_list:
                    if '*' in _filter:
                        _filter = _filter.replace('*', '.')
                        regex_filter = fr'.*{_filter}.*'
                        memes = memes.filter(name__iregex=regex_filter)
                        flag_regex = True
                    else:
                        memes = memes.filter(name__icontains=_filter)

        if filter_user:
            memes = memes.filter(author=filter_user)

        if len(memes) == 0:
            raise PWarning("Не нашёл :(")
        elif len(memes) == 1:
            return memes.first()
        elif not approved:
            return memes.first()
        else:
            filters_str = " ".join(filter_list)
            for meme in memes:
                if meme.name == filters_str:
                    return meme
                if flag_regex and len(meme.name) == len(filters_str):
                    return meme
            if not use_tanimoto:
                msg = self.get_similar_memes_names(memes)
                raise PWarning(msg)
            else:
                filters_str = " ".join(filter_list)
                return get_tanimoto_memes(memes, filters_str)

    @staticmethod
    def get_random_meme():
        return MemeModel.objects.filter(approved=True).order_by('?').first()

    def prepare_meme_to_send(self, meme, print_name=False, send_keyboard=False):
        prepared_meme = prepare_meme_to_send(self.bot, self.event, meme, print_name, send_keyboard, self.name)
        if send_keyboard:
            prepared_meme['keyboard'] = self.bot.get_inline_keyboard(
                [{'command': self.name, 'button_text': "Ещё", 'args': ["р"]}])
        return prepared_meme

    @staticmethod
    def get_similar_memes_names(memes):
        total_memes_count = len(memes)
        memes = memes[:10]
        meme_names = []
        for meme in memes:
            if len(meme.name) < 50:
                meme_names.append(meme.name)
            else:
                meme_names.append(meme.name[:50] + "...")
        meme_names_str = ";\n".join(meme_names)

        msg = f"Нашёл сразу {total_memes_count}, уточните:\n\n" \
              f"{meme_names_str}" + '.'
        if total_memes_count > 10:
            msg += "\n..."
        return msg


def get_tanimoto_memes(memes, query):
    memes_list = []
    for meme in memes:
        tanimoto_coefficient = tanimoto(meme.name, query)
        memes_list.append({'meme': meme, 'tanimoto': tanimoto_coefficient, 'contains_query': query in meme.name})
    memes_list.sort(key=lambda x: (x['contains_query'], x['tanimoto']), reverse=True)
    memes_list = [meme['meme'] for meme in memes_list]
    return memes_list


def prepare_meme_to_send(bot, event, meme, print_name=False, send_keyboard=False, name=None):
    msg = {}

    if event.platform == Platform.TG:
        if meme.type == 'photo':
            msg['attachments'] = bot.upload_photos(meme.link)
        else:
            msg['text'] = meme.link
        if meme.type == 'link':
            msg['attachments'] = meme.link
    elif event.platform == Platform.VK:
        if meme.type == 'video':
            msg['attachments'] = [meme.link.replace(VK_URL, '')]
            # Проверяем не удалено ли видео
            owner_id, _id = msg['attachments'][0].replace('video', '').split('_')
            if bot.get_video(owner_id, _id)['count'] == 0:
                error = "Мем был удалён, перезалейте плиз"
                meme_info = meme.get_info()
                message_to_test_chat = f"{error}\n\n{meme_info}"
                bot.parse_and_send_msgs(bot.test_chat.chat_id, message_to_test_chat)
                raise PWarning(error)
        elif meme.type == 'link':
            msg['text'] = meme.link
        elif meme.type == 'audio':
            msg['attachments'] = [meme.link.replace(VK_URL, '')]
        elif meme.type == 'photo':
            msg['attachments'] = bot.upload_photos(meme.link)

        else:
            raise PError("У мема нет типа. Тыкай разраба")

    if print_name:
        if msg.get('text', None):
            msg['text'] += f"\n{meme.name}"
    return msg
