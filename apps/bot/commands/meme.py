import threading
from typing import List
from urllib.parse import urlparse

import requests

from apps.bot.api.youtube.video import YoutubeVideo
from apps.bot.classes.bots.bot import send_message_to_moderator_chat
from apps.bot.classes.command import AcceptExtraCommand
from apps.bot.classes.const.consts import Role, Platform, ATTACHMENT_TYPE_TRANSLATOR
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.classes.event.event import Event
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.gif import GifAttachment
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.attachments.sticker import StickerAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.attachments.videonote import VideoNoteAttachment
from apps.bot.classes.messages.attachments.voice import VoiceAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.utils import tanimoto
from apps.service.models import Meme as MemeModel


class Meme(AcceptExtraCommand):
    name = "мем"

    help_text = HelpText(
        commands_text="присылает мем",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand(None, "присылает рандомный мем"),
                HelpTextItemCommand(
                    "(название/id)",
                    "присылает нужный мем. Можно использовать * вместо символов поиска. Например /мем ж*па"),
                HelpTextItemCommand(
                    "добавить (название) (Вложение/Пересланное сообщение с вложением)",
                    "добавляет мем"),
                HelpTextItemCommand("добавить (название) (ссылка на youtube/coub) ", "добавляет мем с youtube/coub"),
                HelpTextItemCommand(
                    "обновить (название/id) (Вложение/Пересланное сообщение с вложением)",
                    "обновляет созданный вами мем."),
                HelpTextItemCommand("обновить (название/id) (ссылка на youtube/coub)", "обновляет созданный вами мем"),
                HelpTextItemCommand("удалить (название/id)", "удаляет созданный вами мем"),
                HelpTextItemCommand("инфо (название/id)", "присылает информацию по мему")
            ]),
            HelpTextItem(Role.MODERATOR, [
                HelpTextItemCommand("подтвердить", "присылает мем на подтверждение"),
                HelpTextItemCommand("подтвердить (название/id)", "подтверждает мем"),
                HelpTextItemCommand("отклонить (название/id)", "отклоняет мем"),
                HelpTextItemCommand("переименовать (id) (новое название)", "переименовывает мем"),
                HelpTextItemCommand("удалить (название/id)", "удаляет мем")
            ])
        ],
        extra_text=(
            "Поддерживается добавление/обновление мемов с нарезкой по аналогии с командами /Медиа и /Нарезка\n\n"
            "Если вы хотите отправлять мемы в любые чаты через @, но бот в предложенном списке не всплывает, то зайдите в"
            "настройки телеги с телефона (это важно) -> Конфиденциальность -> Панель контакты -> "
            "Подсказка людей при поиске. После чего вручную введите имя бота @igor_petrovich_ksta_bot и отправьте 1 мем "
            "в любой чат. После этого вы сможете быстро находить бота через @ и выбирать его"
        )
    )

    priority = 70

    ALLOWED_ATTACHMENTS = [
        PhotoAttachment, VideoAttachment, StickerAttachment, GifAttachment, VoiceAttachment, VideoNoteAttachment,
        LinkAttachment
    ]

    platforms = [Platform.TG]

    @staticmethod
    def accept_extra(event: Event) -> bool:
        if event.is_fwd:
            return False
        if event.message and not event.message.mentioned:
            if event.sender.settings.need_meme and not event.message.mentioned:
                message_is_exact_meme_name = MemeModel.objects.filter(name=event.message.clear, approved=True).exists()
                if message_is_exact_meme_name:
                    return True
        return False

    def start(self) -> ResponseMessage:
        if self.event.command == self.__class__:
            self.event.message.args = self.event.message.clear.split(' ')

        if not self.event.message.args:
            return self.menu_random()

        arg0 = self.event.message.args[0]
        menu = [
            [['добавить'], self.menu_add],
            [['обновить'], self.menu_refresh],
            [['удалить'], self.menu_delete],
            [['подтвердить', 'принять', '+'], self.menu_approve],
            [['отклонить', 'отменить', '-'], self.menu_reject],
            [['переименовать', 'правка'], self.menu_rename],
            [['инфо'], self.menu_info],
            [['default'], self.menu_default]
        ]
        method = self.handle_menu(menu, arg0)
        return method()

    # MENU #

    def menu_add(self) -> ResponseMessage:
        self.check_args(2)
        attachments = self.event.get_all_attachments(self.ALLOWED_ATTACHMENTS)
        if len(attachments) == 0:
            raise PWarning("Не нашёл вложений в сообщении")
        attachment = attachments[0]

        meme_name_list = self.event.message.args[1:]
        if isinstance(attachment, LinkAttachment):
            self._check_allowed_url(attachment)
            att_url_lower = attachment.url.lower()
            if not self.event.fwd and att_url_lower in meme_name_list:
                meme_name_list = meme_name_list[:meme_name_list.index(att_url_lower)]

        meme_name = " ".join(meme_name_list)
        self.check_meme_name(meme_name_list)

        new_meme = {
            'name': meme_name,
            'type': attachment.type,
            'author': self.event.sender,
            'approved': self.event.sender.check_role(Role.MODERATOR) or self.event.sender.check_role(Role.TRUSTED)
        }

        try:
            MemeModel.objects.get(name=new_meme['name'])
            raise PWarning("Мем с таким названием уже есть в базе")
        except MemeModel.DoesNotExist:
            pass

        if isinstance(attachment, LinkAttachment):
            new_meme['link'] = attachment.url
        else:
            new_meme['tg_file_id'] = attachment.file_id
        new_meme_obj = MemeModel.objects.create(**new_meme)

        # Кэш
        if isinstance(attachment, LinkAttachment) and attachment.is_youtube_link:
            self.set_youtube_file_id(new_meme_obj)
        if new_meme['approved']:
            answer = "Добавил"
            return ResponseMessage(ResponseMessageItem(text=answer))

        meme_to_send = self.prepare_meme_to_send(new_meme_obj)
        meme_to_send.text = "Запрос на подтверждение мема:\n" \
                            f"{new_meme_obj.author}\n" \
                            f"{new_meme_obj.name} ({new_meme_obj.id})"

        button_approve = self.bot.get_button("Подтвердить", self.name, args=["подтвердить", new_meme_obj.pk])
        button_decline = self.bot.get_button("Отклонить", self.name, args=["отклонить", new_meme_obj.pk])
        meme_to_send.keyboard = self.bot.get_inline_keyboard([button_approve, button_decline])

        # Отправка сообщения в модераторную
        send_message_to_moderator_chat(meme_to_send)
        answer = "Добавил. Воспользоваться мемом можно после проверки модераторами."
        return ResponseMessage(ResponseMessageItem(text=answer))

    def menu_refresh(self) -> ResponseMessage:
        self.check_args(2)
        attachments = self.event.get_all_attachments(self.ALLOWED_ATTACHMENTS)
        if len(attachments) == 0:
            raise PWarning("Не нашёл вложений в сообщении")
        attachment = attachments[0]
        id_name_list = self.event.message.args[1:]

        if isinstance(attachment, LinkAttachment):
            self._check_allowed_url(attachment)
            att_url_lower = attachment.url.lower()
            if not self.event.fwd and att_url_lower in id_name_list:
                id_name_list = id_name_list[:id_name_list.index(att_url_lower)]
        id_name = self.get_id_or_meme_name(id_name_list)

        meme_filter = {}
        if isinstance(id_name, int):
            meme_filter['_id'] = id_name
        else:
            meme_filter['filter_list'] = id_name.split(' ')
        if not (self.event.sender.check_role(Role.MODERATOR) or self.event.sender.check_role(Role.TRUSTED)):
            meme_filter['filter_user'] = self.event.sender
        if not self.event.sender.check_role(Role.TRUSTED):
            meme_filter['exclude_trusted'] = True

        meme = self.get_meme(**meme_filter)

        fields = {'type': attachment.type}
        if isinstance(attachment, LinkAttachment):
            fields['link'] = attachment.url
        else:
            fields['tg_file_id'] = attachment.file_id

        for attr, value in fields.items():
            setattr(meme, attr, value)

        # Кэш
        if self.event.sender.check_role(Role.MODERATOR) or \
                self.event.sender.check_role(Role.TRUSTED):
            meme.save()
            if isinstance(attachment, LinkAttachment) and attachment.is_youtube_link:
                self.set_youtube_file_id(meme)
            answer = f'Обновил мем "{meme.name}"'
            return ResponseMessage(ResponseMessageItem(text=answer))

        meme_to_send = self.prepare_meme_to_send(meme)
        meme_to_send.text = "Запрос на обновление мема:\n" \
                            f"{meme.author}\n" \
                            f"{meme.name} ({meme.id})"
        if meme.link:
            meme_to_send.text += f"\n{meme.link}"
        send_message_to_moderator_chat(meme_to_send)

        answer = "Обновил. Воспользоваться мемом можно после проверки модераторами."
        return ResponseMessage(ResponseMessageItem(text=answer))

    def menu_delete(self) -> ResponseMessage:
        self.check_args(2)
        meme_filter = self.get_default_meme_filter_by_args(self.event.message.args[1:])
        if not self.event.sender.check_role(Role.MODERATOR):
            meme_filter['filter_user'] = self.event.sender
        if not self.event.sender.check_role(Role.TRUSTED):
            meme_filter['exclude_trusted'] = True
        meme = self.get_meme(**meme_filter)

        if not self.event.sender.check_role(Role.MODERATOR) and meme.author != self.event.sender:
            raise PWarning("У вас нет прав на удаление мемов")
        # Если удаляем мем другого человека, шлём ему сообщением

        rm = ResponseMessage()
        if meme.author and meme.author != self.event.sender:
            user_msg = f'Мем с названием "{meme.name}" удалён поскольку он не ' \
                       f'соответствует правилам, устарел или является дубликатом.'
            user = meme.author.get_tg_user()
            rmi = ResponseMessageItem(
                text=user_msg,
                peer_id=user.user_id,
                message_thread_id=self.event.message_thread_id)
            self.bot.send_response_message_item(rmi)
            rmi.send = False
            rm.messages.append(rmi)

        meme_name = meme.name
        meme.delete()
        answer = f'Удалил мем "{meme_name}"'
        rm.messages.append(ResponseMessageItem(text=answer))
        return rm

    def menu_random(self) -> ResponseMessage:
        memes = MemeModel.objects.filter(approved=True)
        if not self.event.sender.check_role(Role.TRUSTED):
            memes = memes.exclude(for_trusted=True)
        meme = memes.order_by('?').first()
        rmi = self.prepare_meme_to_send(meme, print_name=True, send_keyboard=True)
        return ResponseMessage(rmi)

    def menu_approve(self) -> ResponseMessage:
        self.check_sender(Role.MODERATOR)

        if len(self.event.message.args) == 1:
            meme = self.get_meme(approved=False)
            rmi = self.prepare_meme_to_send(meme)
            rmi.text = f"{meme.author}\n" \
                       f"{meme.name} ({meme.id})"
            return ResponseMessage(rmi)

        self.check_args(2)

        meme_filter = self.get_default_meme_filter_by_args(self.event.message.args[1:])
        meme = self.get_meme(**meme_filter)

        if meme.approved:
            raise PWarning("Мем уже подтверждён")

        answer = f'Мем с названием "{meme.name}" подтверждён.'
        user = meme.author.get_tg_user()

        meme.approved = True
        meme.save()
        return ResponseMessage([
            ResponseMessageItem(text=answer),
            ResponseMessageItem(text=answer, peer_id=user.user_id)
        ])

    def menu_reject(self) -> ResponseMessage:
        self.check_sender(Role.MODERATOR)
        self.check_args(2)

        meme_filter = self.get_default_meme_filter_by_args(self.event.message.args[1:])
        meme = self.get_meme(**meme_filter)
        if meme.approved:
            raise PWarning("Нельзя отклонить уже подтверждённый мем")

        answer = f'Мем "{meme.name}" ({meme.id}) отклонён'
        user = meme.author.get_tg_user()

        meme.delete()
        return ResponseMessage([
            ResponseMessageItem(text=answer),
            ResponseMessageItem(
                text=answer,
                peer_id=user.user_id
            )
        ])

    def menu_rename(self) -> ResponseMessage:
        self.check_sender(Role.MODERATOR)
        self.check_args(3)
        self.int_args = [1]
        self.parse_int()
        exclude_trusted = False
        if not self.event.sender.check_role(Role.TRUSTED):
            exclude_trusted = True
        meme = self.get_meme(_id=self.event.message.args[1], exclude_trusted=exclude_trusted)

        new_name_list = self.event.message.args[2:]
        new_name = " ".join(new_name_list)
        self.check_meme_name(new_name)

        try:
            MemeModel.objects.get(name=new_name)
            raise PWarning("Мем с таким названием уже есть")
        except MemeModel.DoesNotExist:
            pass

        user_msg = f'Мем с названием "{meme.name}" переименован.\n' \
                   f'Новое название - "{new_name}"'

        meme.name = new_name
        meme.save()

        rm = ResponseMessage()
        rm.messages.append(ResponseMessageItem(text=user_msg))
        if meme.author != self.event.sender:
            user = meme.author.get_tg_user()
            rmi = ResponseMessageItem(
                text=user_msg,
                peer_id=user.user_id
            )
            rm.messages.append(rmi)
        return rm

    def menu_info(self) -> ResponseMessage:
        self.check_args(2)
        meme_filter = self.get_default_meme_filter_by_args(self.event.message.args[1:])
        exclude_trusted = False
        if not self.event.sender.check_role(Role.TRUSTED):
            exclude_trusted = True
        meme = self.get_meme(**meme_filter, exclude_trusted=exclude_trusted)
        answer = meme.get_info()
        return ResponseMessage(ResponseMessageItem(text=answer))

    def menu_default(self) -> ResponseMessage:
        warning_message = None

        exclude_trusted = False
        if not self.event.sender.check_role(Role.TRUSTED):
            exclude_trusted = True

        id_name = self.get_id_or_meme_name(self.event.message.args)
        if isinstance(id_name, int):
            meme = self.get_meme(_id=id_name, exclude_trusted=exclude_trusted)
        else:
            memes = self.get_filtered_memes(self.event.message.args, exclude_trusted=exclude_trusted)
            try:
                meme = self.get_one_meme(memes, self.event.message.args)
            except PWarning:
                tanimoto_memes = self.get_tanimoto_memes(memes, " ".join(self.event.message.args))
                if len(tanimoto_memes) == 0:
                    raise PWarning("Не нашёл :(")
                meme = tanimoto_memes[0]
                warning_message = self.get_similar_memes_names(tanimoto_memes)

        meme.uses += 1
        meme.save()
        rm = ResponseMessage()
        rm.messages.append(self.prepare_meme_to_send(meme))
        if warning_message:
            rm.messages.append(warning_message)
        return rm

    @staticmethod
    def get_filtered_memes(filter_list=None, filter_user=None, exclude_trusted=False, approved=True, _id=None):
        memes = MemeModel.objects
        if exclude_trusted:
            memes = memes.exclude(for_trusted=True)

        if _id:
            memes = memes.filter(id=_id)
        else:
            if filter_list is None:
                filter_list = []
            memes = memes.filter(approved=approved)
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

    @staticmethod
    def get_one_meme(memes, filter_list, approved=True) -> MemeModel:
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

    def get_meme(self, filter_list=None, filter_user=None, exclude_trusted=False, approved=True, _id=None) -> MemeModel:
        """
        :return: 1 мем. Если передан параметр use_tanimoto, то список мемов отсортированных по коэфф. Танимото
        """
        memes = self.get_filtered_memes(filter_list, filter_user, exclude_trusted, approved, _id)
        meme = self.get_one_meme(memes, filter_list, approved)
        return meme

    def prepare_meme_to_send(self, meme, print_name=False, send_keyboard=False) -> ResponseMessageItem:
        rmi = ResponseMessageItem()
        if meme.tg_file_id:
            att = ATTACHMENT_TYPE_TRANSLATOR[meme.type]()
            att.file_id = meme.tg_file_id
            rmi.attachments = [att]
        else:
            rmi.text = meme.link

        if print_name and rmi.text:
            rmi.text += f"\n{meme.name}"

        if send_keyboard:
            button = self.bot.get_button("Ещё", self.name)
            button2 = self.bot.get_button("Инфо", self.name, args=["инфо", meme.pk])
            rmi.keyboard = self.bot.get_inline_keyboard([button, button2], cols=2)
        return rmi

    @staticmethod
    def _check_allowed_url(attachment):
        if not attachment.is_youtube_link:
            raise PWarning("Это ссылка не на youtube видео")

    def set_youtube_file_id(self, meme):
        thread = threading.Thread(target=self._set_youtube_file_id, args=(meme,))
        thread.start()

    def _set_youtube_file_id(self, meme):
        from apps.bot.commands.trim_video import TrimVideo

        lower_link_index = self.event.message.args.index(meme.link.lower())
        args = self.event.message.args[lower_link_index + 1:]
        start_pos, end_pos = TrimVideo.get_timecodes(meme.link, args)
        try:
            # Если видео надо нарезать
            if start_pos:
                tm = TrimVideo()
                video_content = tm.trim_link_pos(meme.link, start_pos, end_pos)
            else:
                yt_api = YoutubeVideo()
                data = yt_api.get_video_info(meme.link)
                video_content = requests.get(data['download_url']).content
            video = self.bot.get_video_attachment(video_content)
            parsed_url = urlparse(meme.link)
            video_id = parsed_url.path.strip('/')
            video.thumb = f"https://img.youtube.com/vi/{video_id}/default.jpg"

            meme.tg_file_id = video.get_file_id()
            meme.type = VideoAttachment.TYPE
            meme.save()
            return
        except Exception:
            return

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
    def get_similar_memes_names(memes) -> ResponseMessageItem:
        meme_name_limit = 120
        meme_count_limit = 20
        total_memes_count = len(memes)
        memes = memes[:meme_count_limit]
        meme_names = []
        for meme in memes:
            if len(meme.name) < meme_name_limit:
                meme_names.append(meme.name)
            else:
                meme_names.append(meme.name[:meme_name_limit] + "...")
        meme_names_str = ";\n".join(meme_names)

        answer = f"Нашёл сразу {total_memes_count}, уточните:\n\n" \
                 f"{meme_names_str}" + '.'
        if total_memes_count > meme_count_limit:
            answer += "\n..."
        return ResponseMessageItem(text=answer)

    @staticmethod
    def get_id_or_meme_name(args):
        """
        Возвращает int если это id и передан только один аргумент.
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

    @staticmethod
    def check_meme_name(name):
        ban_list = ['добавить', 'обновить', 'удалить', 'конфа', 'рандом', 'р', 'подтвердить', 'принять', '+',
                    'отклонить', 'отменить', '-', 'переименовать', 'правка', 'инфо']
        if name in ban_list:
            raise PWarning("Мем с таким названием нельзя создать")

        try:
            _ = [int(x) for x in name]
            raise PWarning("Название мема не может состоять только из цифр")
        except ValueError:
            pass

    @staticmethod
    def _get_inline_qrs(memes):
        _inline_qr = []

        att_type_map = {
            PhotoAttachment.TYPE: 'photo_file_id',
            StickerAttachment.TYPE: 'sticker_file_id',
            VideoAttachment.TYPE: 'video_file_id',
            GifAttachment.TYPE: 'gif_file_id',
            VoiceAttachment.TYPE: 'voice_file_id',
        }

        for meme in memes:
            qr = {
                'id': meme.pk,
                'type': meme.type,
                att_type_map[meme.type]: meme.tg_file_id
            }
            if meme.type in [VideoAttachment.TYPE, GifAttachment.TYPE, VoiceAttachment.TYPE]:
                qr.update({
                    'title': meme.name,
                })
            _inline_qr.append(qr)
        return _inline_qr

    def get_tg_inline_memes(self, filter_list, max_count=10):
        if filter_list:
            filtered_memes = self.get_filtered_memes(filter_list)
        else:
            filtered_memes = MemeModel.objects.all().order_by('-uses')

        memes = filtered_memes.filter(type__in=['photo', 'sticker', 'video', 'voice', 'gif'], approved=True)
        if not self.event.sender.check_role(Role.TRUSTED):
            memes = memes.exclude(for_trusted=True)

        all_memes_qr = []
        try:
            this_meme = self.get_one_meme(memes, filter_list)
            this_meme_qr = self._get_inline_qrs([this_meme])
            all_memes_qr += this_meme_qr
            memes = memes.exclude(pk=this_meme.pk)
        except PWarning:
            pass

        memes = memes[:max_count]
        memes = self.get_tanimoto_memes(memes, filter_list)
        if filter_list:
            for meme in memes:
                meme.inline_uses += 1
                meme.save()

        att_types = [
            VoiceAttachment.TYPE,
            VideoAttachment.TYPE,
            GifAttachment.TYPE,
            StickerAttachment.TYPE,
            PhotoAttachment.TYPE
        ]
        for att_type in att_types:
            all_memes_qr += self._get_inline_qrs(list(filter(lambda x: x.type == att_type, memes)))
        return all_memes_qr
