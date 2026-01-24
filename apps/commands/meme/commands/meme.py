import threading

from django.core.files.base import ContentFile

from apps.bot.consts import Role, Platform, ATTACHMENT_TYPE_TRANSLATOR
from apps.bot.core.bot.bot import send_message_to_moderator_chat
from apps.bot.core.messages.attachments.gif import GifAttachment
from apps.bot.core.messages.attachments.link import LinkAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.attachments.sticker import StickerAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.bot.core.messages.attachments.video_note import VideoNoteAttachment
from apps.bot.core.messages.attachments.voice import VoiceAttachment
from apps.bot.core.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.utils.utils import tanimoto, get_youtube_video_id, detect_ext
from apps.bot.utils.video.video_handler import VideoHandler
from apps.commands.command import Command
from apps.commands.help_text import HelpText, HelpTextItem, HelpTextArgument
from apps.connectors.parsers.media_command.youtube.video import YoutubeVideo
from apps.service.models import Meme as MemeModel
from apps.shared.exceptions import PWarning, PSkip


class Meme(Command):
    name = "мем"

    help_text = HelpText(
        commands_text="присылает мем",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextArgument(None, "присылает рандомный мем"),
                HelpTextArgument(
                    "(название/id)",
                    "присылает нужный мем. Можно использовать * вместо символов поиска. Например /мем ж*па"),
                HelpTextArgument(
                    "добавить (название) (Вложение/Пересланное сообщение с вложением)",
                    "добавляет мем"),
                HelpTextArgument("добавить (название) (ссылка на youtube/coub)", "добавляет мем с youtube/coub"),
                HelpTextArgument(
                    "обновить (название/id) (Вложение/Пересланное сообщение с вложением)",
                    "обновляет созданный вами мем."),
                HelpTextArgument("обновить (название/id) (ссылка на youtube/coub)", "обновляет созданный вами мем"),
                HelpTextArgument("удалить (название/id)", "удаляет созданный вами мем"),
                HelpTextArgument("инфо (название/id)", "присылает информацию по мему")
            ]),
            HelpTextItem(Role.MODERATOR, [
                HelpTextArgument("подтвердить", "присылает мем на подтверждение"),
                HelpTextArgument("подтвердить (название/id)", "подтверждает мем"),
                HelpTextArgument("отклонить (название/id)", "отклоняет мем"),
                HelpTextArgument("переименовать (id) (новое название)", "переименовывает мем"),
                HelpTextArgument("удалить (название/id)", "удаляет мем")
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

    # Обоснование: команда должна обрабатываться после остальных команд так как могут быть мемы пересекающиеся
    #  с названием команд
    priority = -10

    ALLOWED_ATTACHMENTS = [
        PhotoAttachment, VideoAttachment, StickerAttachment, GifAttachment, VoiceAttachment, VideoNoteAttachment,
        LinkAttachment
    ]

    platforms = [Platform.TG]

    MESSAGE_YOUTUBE_STATUS_IN_PROGRESS = "Статус скачивания с ютуба: 🔄 в процессе"
    MESSAGE_YOUTUBE_STATUS_COMPLETE = "Статус скачивания с ютуба: ✅ готово"
    MESSAGE_YOUTUBE_STATUS_ERROR = "Статус скачивания с ютуба: ❌ ошибка"
    MESSAGE_YOUTUBE_STATUS_CUSTOM_ERROR = "Статус скачивания с ютуба: ❌ ошибка ({error_msg})"

    def start(self) -> ResponseMessage:
        # if self.event.command == self.__class__:
        #     self.event.message.args = self.event.message.clear.split(' ')

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
        is_youtube_link = isinstance(attachment, LinkAttachment) and attachment.is_youtube_link
        callback_params_data = {}

        if new_meme['approved']:
            answer = "Добавил"
            if not is_youtube_link:
                self._save_meme(new_meme_obj)
                return ResponseMessage(ResponseMessageItem(text=answer))

            answer_with_youtube = f"{answer}\n{self.MESSAGE_YOUTUBE_STATUS_IN_PROGRESS}"
            response = self.bot.send_response_message_item(
                ResponseMessageItem(text=answer_with_youtube, peer_id=self.event.peer_id)
            )
            callback_params_data = {
                "chat_id": self.event.peer_id,
                "message_id": response.response['result']['message_id'],
                "caption": answer
            }

        if is_youtube_link:
            self.set_youtube_file_id(new_meme_obj, callback_params_data)
        else:
            self._save_meme(new_meme_obj)

        if new_meme['approved']:
            raise PSkip()

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

        is_youtube_link = isinstance(attachment, LinkAttachment) and attachment.is_youtube_link
        callback_params_data = {}

        trusted_user = self.event.sender.check_role(Role.MODERATOR) or self.event.sender.check_role(Role.TRUSTED)
        # Кэш
        if trusted_user:
            meme.save()
            self._save_meme(meme, is_update=True)
            answer = f'Обновил мем "{meme.name}"'
            if not is_youtube_link:
                return ResponseMessage(ResponseMessageItem(text=answer))

            answer_with_youtube = f"{answer}\n{self.MESSAGE_YOUTUBE_STATUS_IN_PROGRESS}"
            response = self.bot.send_response_message_item(
                ResponseMessageItem(text=answer_with_youtube, peer_id=self.event.peer_id)
            )
            callback_params_data = {
                "chat_id": self.event.peer_id,
                "message_id": response.response['result']['message_id'],
                "caption": answer
            }

        if is_youtube_link:
            self.set_youtube_file_id(meme, callback_params_data, is_update=True)

        if trusted_user:
            raise PSkip()

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
        meme.file.delete()
        meme.file_preview.delete()
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

        meme.file.delete()
        meme.file_preview.delete()
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
        if filter_user:
            memes = memes.filter(author=filter_user)
        if exclude_trusted:
            memes = memes.exclude(for_trusted=True)
        if _id:
            return memes.filter(id=_id)
        if filter_list is None:
            filter_list = []
        memes = memes.filter(approved=approved)
        if filter_list:
            filter_list = [x.lower() for x in filter_list]
            for _filter in filter_list:
                if '*' in _filter:
                    _filter = _filter.replace('*', '.')
                    regex_filter = fr'.*{_filter}.*'
                    memes = memes.filter(name__iregex=regex_filter)
                else:
                    memes = memes.filter(name__contains=_filter)
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

    def set_youtube_file_id(self, meme: MemeModel, callback_params_data: dict, is_update: bool = False):
        thread = threading.Thread(target=self._set_youtube_file_id, args=(meme, callback_params_data, is_update))
        thread.start()

    def _set_youtube_file_id(self, meme: MemeModel, callback_params_data: dict, is_update: bool = False):
        from apps.commands.other.commands.trusted.trim_video import TrimVideo

        lower_link_index = self.event.message.args.index(meme.link.lower())
        args = self.event.message.args[lower_link_index + 1:]
        start_pos, end_pos = TrimVideo.get_timecodes(meme.link, args)
        yt_api = YoutubeVideo()
        try:
            # Если видео надо нарезать
            from apps.bot.core.bot.tg_bot.tg_bot import TgBot
            data = yt_api.get_video_info(meme.link)

            if start_pos:
                tm = TrimVideo()
                video_content = tm.trim_link_pos(meme.link, start_pos, end_pos)
            else:
                va = yt_api.download_video(data)
                video_content = va.content
            video = self.bot.get_video_attachment(video_content)
            video.thumbnail_url = data.thumbnail_url
            # зачем?

            meme.tg_file_id = video.get_file_id()
            meme.type = VideoAttachment.TYPE
            meme.save()
            self._save_meme(meme, video_content, is_update=is_update)

            callback_params_data['caption'] += f"\n{self.MESSAGE_YOUTUBE_STATUS_COMPLETE}"
            self.bot.edit_message(callback_params_data)
            return
        except PWarning as e:
            callback_params_data['caption'] = self.MESSAGE_YOUTUBE_STATUS_CUSTOM_ERROR.format(
                error_msg=e.msg
            )
            self.bot.edit_message(callback_params_data)
            return
        except Exception:
            callback_params_data['caption'] = f"\n{self.MESSAGE_YOUTUBE_STATUS_ERROR}"
            self.bot.edit_message(callback_params_data)
            return

    @staticmethod
    def get_tanimoto_memes(memes, filter_list) -> list[MemeModel]:
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
                qr['title'] = meme.name

            # set youtube preview
            if meme.type in [VideoAttachment.TYPE] and meme.link:
                if video_id := get_youtube_video_id(meme.link):
                    qr['thumb_url'] = f"https://img.youtube.com/vi/{video_id}/default.jpg"

            _inline_qr.append(qr)
        return _inline_qr

    @staticmethod
    def _save_meme(meme: MemeModel, content: bytes | None = None, is_update: bool = False):
        # save meme
        att = ATTACHMENT_TYPE_TRANSLATOR[meme.type]()
        att.file_id = meme.tg_file_id
        att.get_file()
        if not content:
            content = att.download_content()
        else:
            att.content = content

        detected_ext = detect_ext(content)
        if not detected_ext:
            raise RuntimeError("Can't detect ext")
        filename = f"{meme.id}.{detected_ext}"
        if is_update:
            meme.file.delete()
        meme.file.save(filename, ContentFile(content))

        # save preview for youtube vieos
        _content = None
        if meme.link:
            if video_id := get_youtube_video_id(meme.link):
                preview_url = f"https://img.youtube.com/vi/{video_id}/default.jpg"
                att_pa = PhotoAttachment()
                att_pa.public_download_url = preview_url
                _content = att_pa.download_content()
            if isinstance(att, VideoAttachment) and not _content:
                vh = VideoHandler(video=att)
                _content = vh.get_preview()
            if _content:
                filename = f"{meme.id}_preview.jpg"

                if is_update:
                    meme.file_preview.delete()
                meme.file_preview.save(filename, ContentFile(_content))

    # --------------------

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
