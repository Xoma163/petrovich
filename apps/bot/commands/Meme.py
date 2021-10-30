from typing import List
from urllib.parse import urlparse

from apps.bot.classes.Command import Command
from apps.bot.classes.bots.Bot import upload_image_to_vk_server, send_message_to_moderator_chat, get_bot_by_platform
from apps.bot.classes.consts.Consts import Role, Platform
from apps.bot.classes.consts.Exceptions import PWarning, PError
from apps.bot.classes.messages.attachments.LinkAttachment import LinkAttachment
from apps.bot.classes.messages.attachments.PhotoAttachment import PhotoAttachment
from apps.bot.classes.messages.attachments.VideoAttachment import VideoAttachment
from apps.bot.utils.utils import get_attachments_from_attachments_or_fwd, tanimoto
from apps.service.models import Meme as MemeModel
from petrovich.settings import VK_URL


class Meme(Command):
    name = "мем"
    help_text = "присылает нужный мем"
    help_texts = [
        "(название/id) - присылает нужный мем. Можно использовать * вместо символов поиска. Например /мем ж*па",
        "добавить (название) (Вложение/Пересланное сообщение с вложением) - добавляет мем",
        "добавить (название) (ссылка на youtube/coub)  - добавляет мем с youtube/coub",
        "обновить (название/id) (Вложение/Пересланное сообщение с вложением) - обновляет созданный вами мем.",
        "обновить (название/id) (ссылка на youtube/coub) - обновляет созданный вами мем",
        "удалить (название/id) - удаляет созданный вами мем",
        "инфо (название/id) - присылает информацию по мему",
        "р - присылает рандомный мем",

        "подтвердить - присылает мем на подтверждение (для модераторов)",
        "подтвердить (название/id) - подтверждает мем (для модераторов)",
        "отклонить (название/id) - отклоняет мем (для модераторов)",
        "переименовать (id) (новое название) - переименовывает мем (для модераторов)",
        "удалить (название/id) - удаляет мем (для модераторов)"
    ]
    args = 1
    platforms = [Platform.VK, Platform.TG]
    priority = 70

    ALLOWED_URLS = ['youtu.be', 'youtube.com', 'coub.com']

    def accept(self, event):
        if event.command:
            event.message.args = event.message.clear.split(' ')
            return True
        return super().accept(event)

    def start(self):
        arg0 = self.event.message.args[0]
        menu = [
            [['добавить'], self.menu_add],
            [['обновить'], self.menu_refresh],
            [['удалить'], self.menu_delete],
            [['рандом', 'р'], self.menu_random],
            [['подтвердить', 'принять', '+'], self.menu_confirm],
            [['отклонить', 'отменить', '-'], self.menu_reject],
            [['переименовать', 'правка'], self.menu_rename],
            [['инфо'], self.menu_info],
            [['default'], self.menu_default]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    def _check_allowed_url(self, url):
        parsed_url = urlparse(url)
        if not parsed_url.hostname:
            raise PWarning("Не нашёл вложений в сообщении или пересланном сообщении. Не нашёл ссылку на youtube видео")

        if parsed_url.hostname.replace('www.', '').lower() not in self.ALLOWED_URLS:
            raise PWarning("Это ссылка не на youtube/coub видео")

    # MENU #

    def menu_add(self):
        self.check_args(2)
        attachments = get_attachments_from_attachments_or_fwd(self.event, [PhotoAttachment])
        if len(attachments) == 0:
            url = self.event.message.args_str_case.split(' ')[1]
            self._check_allowed_url(url)

            attachment = LinkAttachment()
            attachment.url = url
            meme_name = " ".join(self.event.message.args[2:])
        else:
            meme_name = " ".join(self.event.message.args[1:])
            attachment = attachments[0]

        if self.event.platform != Platform.VK and type(attachment) not in [PhotoAttachment, LinkAttachment]:
            raise PWarning('В данной платформе поддерживается добавление только картинок-мемов и youtube/coub ссылок')

        new_meme = {
            'name': meme_name,
            'type': attachment.type,
            'author': self.event.sender,
            'approved': self.event.sender.check_role(Role.MODERATOR) or self.event.sender.check_role(Role.TRUSTED)
        }

        ban_list = ['добавить', 'обновить', 'удалить', 'конфа', 'рандом', 'р', 'подтвердить', 'принять', '+',
                    'отклонить', 'отменить', '-', 'переименовать', 'правка', 'инфо']
        if new_meme['name'] in ban_list:
            raise PWarning("Мем с таким названием нельзя создать")

        try:
            MemeModel.objects.get(name=new_meme['name'])
            raise PWarning("Мем с таким названием уже есть в базе")
        except MemeModel.DoesNotExist:
            pass

        if isinstance(attachment, LinkAttachment):
            new_meme['link'] = attachment.url
        elif isinstance(attachment, PhotoAttachment):  # or attachment.type == 'doc':
            if self.event.platform == Platform.VK:
                new_meme['link'] = attachment.public_download_url
            else:
                new_meme['link'] = upload_image_to_vk_server(attachment.download_content())

        new_meme_obj = MemeModel.objects.create(**new_meme)
        if new_meme['approved']:
            return "Добавил"

        meme_to_send = self.prepare_meme_to_send(new_meme_obj)
        meme_to_send['text'] = "Запрос на подтверждение мема:\n" \
                               f"{new_meme_obj.author}\n" \
                               f"{new_meme_obj.name} ({new_meme_obj.id})"

        # Отправка сообщения в модераторную
        send_message_to_moderator_chat(meme_to_send)
        return "Добавил. Воспользоваться мемом можно после проверки модераторами."

    def menu_refresh(self):
        self.check_args(2)
        try:
            attachment = LinkAttachment()
            attachment.url = self._check_allowed_url(self.event.message.args[-1])
            attachments = [attachment]
            id_name = self.get_id_or_meme_name(self.event.message.args[1:-1])
        except PWarning:
            attachments = get_attachments_from_attachments_or_fwd(self.event, [VideoAttachment, PhotoAttachment])
            id_name = self.get_id_or_meme_name(self.event.message.args[1:])

        if len(attachments) == 0:
            raise PWarning("Не нашёл вложений в сообщении или пересланном сообщении\n"
                           "Не нашёл ссылки на youtube/coub")

        attachment = attachments[0]
        if isinstance(attachment, LinkAttachment):
            new_meme_link = attachment.url
        elif isinstance(attachment, PhotoAttachment):
            if self.event.platform == Platform.VK:
                new_meme_link = attachment.public_download_url
            else:
                new_meme_link = upload_image_to_vk_server(attachment.download_content())
        else:
            raise PWarning("Невозможно")

        meme_filter = {}
        if isinstance(id_name, int):
            meme_filter['_id'] = id_name
        else:
            meme_filter['filter_list'] = id_name.split(' ')
        if not (self.event.sender.check_role(Role.MODERATOR) or self.event.sender.check_role(Role.TRUSTED)):
            meme_filter['filter_user'] = self.event.sender

        meme = self.get_meme(**meme_filter)
        meme.link = new_meme_link
        meme.type = attachment.type
        meme.save()

        if self.event.sender.check_role(Role.MODERATOR) or self.event.sender.check_role(Role.TRUSTED):
            return f'Обновил мем "{meme.name}"'

        meme_to_send = self.prepare_meme_to_send(meme)
        meme_to_send['text'] = "Запрос на обновление мема:\n" \
                               f"{meme.author}\n" \
                               f"{meme.name} ({meme.id})"

        send_message_to_moderator_chat(meme_to_send)

        return "Обновил. Воспользоваться мемом можно после проверки модераторами."

    def menu_delete(self):
        self.check_args(2)
        meme_filter = self.get_default_meme_filter_by_args(self.event.message.args[1:])
        if not self.event.sender.check_role(Role.MODERATOR):
            meme_filter['filter_user'] = self.event.sender
        meme = self.get_meme(**meme_filter)

        # Если удаляем мем другого человека, шлём ему сообщением
        if self.event.sender.check_role(Role.MODERATOR) and meme.author != self.event.sender:
            msg = f'Мем с названием "{meme.name}" удалён поскольку он не ' \
                  f'соответствует правилам или был удалён автором.'
            bot = get_bot_by_platform(meme.author.get_platform_enum())
            bot.parse_and_send_msgs(meme.author.user_id, msg)

        meme_name = meme.name
        meme.delete()
        return f'Удалил мем "{meme_name}"'

    def menu_random(self):
        meme = MemeModel.objects.filter(approved=True).order_by('?').first()
        return self.prepare_meme_to_send(meme, print_name=True, send_keyboard=True)

    def menu_confirm(self):
        self.check_sender(Role.MODERATOR)

        if len(self.event.message.args) == 1:
            meme = self.get_meme(approved=False)
            meme_to_send = self.prepare_meme_to_send(meme)
            meme_to_send['text'] = f"{meme.author}\n" \
                                   f"{meme.name} ({meme.id})"
            return meme_to_send

        self.check_args(2)

        meme_filter = self.get_default_meme_filter_by_args(self.event.message.args[1:])
        meme = self.get_meme(**meme_filter)

        if meme.approved:
            raise PWarning("Мем уже подтверждён")

        user_msg = f'Мем с названием "{meme.name}" подтверждён.'
        bot = get_bot_by_platform(meme.author.get_platform_enum())
        bot.parse_and_send_msgs(meme.author.user_id, user_msg)

        msg = f'Мем "{meme.name}" ({meme.id}) подтверждён'
        meme.approved = True
        meme.save()
        return msg

    def menu_reject(self):
        self.check_sender(Role.MODERATOR)
        self.check_args(2)

        meme_filter = self.get_default_meme_filter_by_args(self.event.message.args[1:])
        meme = self.get_meme(**meme_filter)

        msg = f'Мем "{meme.name}" ({meme.id}) отклонён'
        bot = get_bot_by_platform(meme.author.get_platform_enum())
        bot.parse_and_send_msgs(meme.author.user_id, msg)
        meme.delete()
        return msg

    def menu_rename(self):
        self.check_sender(Role.MODERATOR)
        self.check_args(3)
        self.int_args = [1]
        self.parse_int()
        meme = self.get_meme(_id=self.event.message.args[1])

        new_name = " ".join(self.event.message.args[2:])
        try:
            MemeModel.objects.get(name=new_name)
            raise PWarning("Мем с таким названием уже есть")
        except MemeModel.DoesNotExist:
            pass

        user_msg = f'Мем с названием "{meme.name}" переименован.\n' \
                   f'Новое название - "{new_name}"'

        meme.name = new_name
        meme.save()

        if meme.author != self.event.sender:
            bot = get_bot_by_platform(meme.author.get_platform_enum())
            bot.parse_and_send_msgs(meme.author.user_id, user_msg)
        return user_msg

    def menu_info(self):
        self.check_args(2)
        meme_filter = self.get_default_meme_filter_by_args(self.event.message.args[1:])
        meme = self.get_meme(**meme_filter)
        return meme.get_info()

    def menu_default(self):
        warning_message = None

        id_name = self.get_id_or_meme_name(self.event.message.args)
        if isinstance(id_name, int):
            meme = self.get_meme(_id=id_name)
        else:
            memes = self.get_filtered_memes(self.event.message.args)
            try:
                meme = self.get_one_meme(memes, self.event.message.args)
            except PWarning:
                tanimoto_memes = self.get_tanimoto_memes(memes, " ".join(self.event.message.args))
                meme = tanimoto_memes[0]
                warning_message = self.get_similar_memes_names(tanimoto_memes)

        meme.uses += 1
        meme.save()
        prepared_meme = self.prepare_meme_to_send(meme)
        if warning_message:
            return [prepared_meme, warning_message]
        return prepared_meme

    # END MENU #

    def get_filtered_memes(self, filter_list=None, filter_user=None, approved=True, _id=None):
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
                    else:
                        memes = memes.filter(name__contains=_filter)

        if filter_user:
            memes = memes.filter(author=filter_user)
        return memes

    def get_one_meme(self, memes, filter_list, approved=True) -> MemeModel:
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
            raise PWarning("Под запрос подходит 2 и более мема")

    def get_meme(self, filter_list=None, filter_user=None, approved=True, _id=None) -> MemeModel:
        """
        :return: 1 мем. Если передан параметр use_tanimoto, то список мемов отсортированных по коэфф. Танимото
        """
        memes = self.get_filtered_memes(filter_list, filter_user, approved, _id)
        meme = self.get_one_meme(memes, filter_list, approved)
        return meme

    def prepare_meme_to_send(self, meme, print_name=False, send_keyboard=False):
        msg = {}

        if self.event.platform == Platform.TG:
            if meme.type == 'photo':
                msg['attachments'] = self.bot.upload_photos(meme.link, peer_id=self.event.peer_id)
            else:
                msg['text'] = meme.link
            if meme.type == 'link':
                msg['attachments'] = meme.link
        elif self.event.platform == Platform.VK:
            if meme.type == 'video':
                msg['attachments'] = [meme.link.replace(VK_URL, '')]
                # Проверяем не удалено ли видео
            elif meme.type == 'link':
                msg['text'] = meme.link
            elif meme.type == 'audio':
                msg['attachments'] = [meme.link.replace(VK_URL, '')]
            elif meme.type == 'photo':
                msg['attachments'] = self.bot.upload_photos(meme.link, peer_id=self.event.peer_id)

            else:
                raise PError("У мема нет типа. Тыкай разраба")

        if print_name:
            if msg.get('text', None):
                msg['text'] += f"\n{meme.name}"
        # return msg

        # ToDo: удалить когда не будет БУНДа
        if meme.type == 'video':
            msg['text'] = f"Ваш мем я нашёл, но я вам его не отдам. Обновите мем на ютуб-ссылку, пожалуйста\n" \
                          f"id={meme.pk}"
        if send_keyboard:
            msg['keyboard'] = self.bot.get_inline_keyboard(
                [{'command': self.name, 'button_text': "Ещё", 'args': ["р"]}])
        return msg

    @staticmethod
    def get_tanimoto_memes(memes, filter_list) -> List[MemeModel]:
        query = " ".join(filter_list)
        memes_list = []
        for meme in memes:
            tanimoto_coefficient = tanimoto(meme.name, query)
            memes_list.append({'meme': meme, 'tanimoto': tanimoto_coefficient, 'contains_query': query in meme.name})
        memes_list.sort(key=lambda x: (x['contains_query'], x['tanimoto']), reverse=True)
        memes_list = [meme['meme'] for meme in memes_list]
        return memes_list

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

    @staticmethod
    def get_id_or_meme_name(args):
        """
        Возвращает int если это id и передан только один аргумент
        Возвращает str если это name
        """
        if isinstance(args, str):
            args = [args]
        if len(args) == 1:
            try:
                _id = int(args[0])
                return _id
            except ValueError:
                pass
        return " ".join(args)

    def get_default_meme_filter_by_args(self, args):
        id_name = self.get_id_or_meme_name(args)

        meme_filter = {}
        if isinstance(id_name, int):
            meme_filter['_id'] = id_name
        else:
            meme_filter['filter_list'] = id_name.split(' ')
        return meme_filter
