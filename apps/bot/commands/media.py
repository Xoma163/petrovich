import json
import re
from io import BytesIO
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from twitchdl import twitch
from twitchdl.commands.download import get_clip_authenticated_url

from apps.bot.api.facebook import Facebook
from apps.bot.api.instagram import Instagram, InstagramAPIData, InstagramAPIDataItem
from apps.bot.api.pikabu import Pikabu
from apps.bot.api.pinterest import Pinterest, PinterestDataItem
from apps.bot.api.premier import Premier
from apps.bot.api.reddit import Reddit
from apps.bot.api.spotify import Spotify
from apps.bot.api.tiktok import TikTok
from apps.bot.api.twitter import Twitter
from apps.bot.api.vk.video import VKVideo
from apps.bot.api.yandex.music import YandexMusicAPI, YandexAlbum, YandexTrack
from apps.bot.api.youtube.music import YoutubeMusic
from apps.bot.api.youtube.video import YoutubeVideo
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.command import Command
from apps.bot.classes.const.activities import ActivitiesEnum
from apps.bot.classes.const.consts import Platform, Role
from apps.bot.classes.const.exceptions import PWarning, PSkip
from apps.bot.classes.event.event import Event
from apps.bot.classes.help_text import HelpText, HelpTextItem, HelpTextItemCommand
from apps.bot.classes.messages.attachments.link import LinkAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.classes.messages.response_message import ResponseMessageItem, ResponseMessage
from apps.bot.commands.trim_video import TrimVideo
from apps.bot.utils.utils import get_urls_from_text, markdown_to_html, retry, markdown_wrap_symbols, get_default_headers
from apps.bot.utils.video.video_handler import VideoHandler
from apps.service.models import VideoCache
from petrovich.settings import MAIN_SITE

YOUTUBE_URLS = ('www.youtube.com', 'youtube.com', "www.youtu.be", "youtu.be", "m.youtube.com")
YOUTUBE_MUSIC_URLS = ("music.youtube.com",)
REDDIT_URLS = ("www.reddit.com", "reddit.com")
TIKTOK_URLS = ("www.tiktok.com", 'vm.tiktok.com', 'm.tiktok.com', 'vt.tiktok.com')
INSTAGRAM_URLS = ('www.instagram.com', 'instagram.com')
TWITTER_URLS = ('www.twitter.com', 'twitter.com', 'x.com')
PIKABU_URLS = ('www.pikabu.ru', 'pikabu.ru')
YANDEX_MUSIC_URLS = ('music.yandex.ru',)
PINTEREST_URLS = ('pinterest.com', 'ru.pinterest.com', 'www.pinterest.com', 'pin.it')
COUB_URLS = ('coub.com',)
VK_URLS = ('vk.com',)
SCOPE_GG_URLS = ('app.scope.gg',)
CLIPS_TWITCH_URLS = ('clips.twitch.tv',)
FACEBOOK_URLS = ('www.facebook.com', 'facebook.com', 'fb.watch')
PREMIERE_URLS = ('premier.one',)
SPOTIFY_URLS = ('open.spotify.com',)

MEDIA_URLS = tuple(
    YOUTUBE_URLS +
    YOUTUBE_MUSIC_URLS +
    REDDIT_URLS +
    TIKTOK_URLS +
    INSTAGRAM_URLS +
    TWITTER_URLS +
    PIKABU_URLS +
    YANDEX_MUSIC_URLS +
    PINTEREST_URLS +
    COUB_URLS +
    VK_URLS +
    SCOPE_GG_URLS +
    CLIPS_TWITCH_URLS +
    FACEBOOK_URLS +
    PREMIERE_URLS +
    SPOTIFY_URLS
)


class Media(Command):
    name = "медиа"
    names = ["media"]

    help_text = HelpText(
        commands_text="скачивает видео/фото из соцсетей и присылает его",
        help_texts=[
            HelpTextItem(Role.USER, [
                HelpTextItemCommand("(ссылка на видео/пост)", "скачивает видео из соцсетей и присылает его")
            ])
        ],
        extra_text=(
            "Поддерживаемые соцсети: Youtube/Youtube Music/Reddit/TikTok/Instagram/Twitter/Pikabu/"
            "Yandex Music/Pinterest/Coub/VK Video/ScopeGG/TwitchClips/Facebook video/Premier/Spotify\n\n"
            "Ключ --nomedia позволяет не запускать команду\n"
            "Ключ --audio позволяет скачивать аудиодорожку для видео с ютуба\n"
            "Ключ --thread позволяет скачивать пост с комментариями автора для твиттера\n\n"
            "Видосы из ютуба качаются автоматически только если длина ролика менее 2 минут. \n"
            "Вручную с указанием команды - скачается\n\n"
            "Некоторые сервисы доступны только доверенным пользователям: Twitter/Instagram/Yandex Music"
        )
    )

    platforms = [Platform.TG]
    attachments = [LinkAttachment]

    bot: TgBot

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_command_name = None

    @staticmethod
    def accept_extra(event: Event) -> bool:
        if event.message and not event.message.mentioned:
            if "nomedia" in event.message.keys or "no-media" in event.message.keys:
                return False
            all_urls = get_urls_from_text(event.message.clear_case)
            has_fwd_with_message = event.fwd and event.fwd[0].message and event.fwd[0].message.clear_case
            if event.is_from_pm and has_fwd_with_message:
                all_urls += get_urls_from_text(event.fwd[0].message.clear_case)
            for url in all_urls:
                message_is_media_link = urlparse(url).hostname in MEDIA_URLS
                if message_is_media_link:
                    return True
        return False

    def start(self) -> ResponseMessage:
        if self.event.message.command in self.full_names:
            if self.event.message.args or self.event.fwd:
                source = self.event.get_all_attachments([LinkAttachment])[0].url
            else:
                raise PWarning("Для работы команды требуются аргументы или пересылаемые сообщения")
            self.has_command_name = True
        else:
            source = self.event.get_all_attachments([LinkAttachment])[0].url
            self.has_command_name = False

        method, chosen_url = self.get_method_and_chosen_url(source)

        try:
            attachments, title = method(chosen_url)
        except PWarning as e:
            # Если была вызвана команда или отправлено сообщение в лс
            if self.has_command_name or self.event.is_from_pm:
                raise e
            else:
                raise PSkip()

        answer = ""
        if title:
            answer = f"{markdown_wrap_symbols(title)}\n"
        if self.event.is_from_chat:
            answer += f"\nОт {self.event.sender}"

        source_hostname = str(urlparse(chosen_url).hostname).lstrip('www.')
        answer += f'\nИсточник: {self.bot.get_formatted_url(source_hostname, chosen_url)}'

        reply_to = self.event.fwd[0].message.id if self.event.fwd else None

        rmi = ResponseMessageItem(
            text=answer,
            attachments=attachments,
            reply_to=reply_to,
            peer_id=self.event.peer_id,
            message_thread_id=self.event.message_thread_id
        )
        br = self.bot.send_response_message_item(rmi)
        if br.success:
            self.bot.delete_messages(self.event.peer_id, self.event.message.id)
        return ResponseMessage(rmi, send=False)

    def get_method_and_chosen_url(self, source):
        media_translator = {
            YOUTUBE_URLS: self.get_youtube_video,
            YOUTUBE_MUSIC_URLS: self.get_youtube_audio,
            TIKTOK_URLS: self.get_tiktok_video,
            REDDIT_URLS: self.get_reddit_content,
            INSTAGRAM_URLS: self.get_instagram_attachment,
            TWITTER_URLS: self.get_twitter_content,
            PIKABU_URLS: self.get_pikabu_video,
            YANDEX_MUSIC_URLS: self.get_yandex_music,
            PINTEREST_URLS: self.get_pinterest_attachment,
            COUB_URLS: self.get_coub_video,
            VK_URLS: self.get_vk_video,
            SCOPE_GG_URLS: self.get_scope_gg_video,
            CLIPS_TWITCH_URLS: self.get_clips_twitch_video,
            FACEBOOK_URLS: self.get_facebook_video,
            PREMIERE_URLS: self.get_premiere_video,
            SPOTIFY_URLS: self.get_spotify_music,
        }

        urls = get_urls_from_text(source)
        for url in urls:
            hostname = urlparse(url).hostname
            if not hostname:
                raise PWarning("Не нашёл ссылки")
            for k in media_translator:
                if hostname in k:
                    return media_translator[k], url

        raise PWarning("Не медиа ссылка")

    @retry(3, Exception, sleep_time=2)
    def get_youtube_video(self, url) -> (list, str):
        if 'audio' in self.event.message.keys:
            return self.get_youtube_audio(url)

        max_filesize_mb = self.bot.MAX_VIDEO_SIZE_MB if isinstance(self.bot, TgBot) else None
        yt_api = YoutubeVideo()

        args = self.event.message.args[1:] if self.event.message.command in self.full_names else self.event.message.args
        end_pos = None
        try:
            start_pos, end_pos = TrimVideo.get_timecodes(url, args)
        except ValueError:
            start_pos = None

        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
            if start_pos:
                tm = TrimVideo()
                video_content = tm.trim_link_pos(url, start_pos, end_pos)
                va = self.bot.get_video_attachment(video_content, peer_id=self.event.peer_id)
                text = None
            else:
                data = yt_api.get_video_info(url, max_filesize_mb=max_filesize_mb)
                if not self.has_command_name and data['duration'] > 120:
                    button = self.bot.get_button(f"{self.event.message.COMMAND_SYMBOLS[0]}{self.name} {url}")
                    keyboard = self.bot.get_inline_keyboard([button])
                    raise PWarning(
                        "Видосы до 2х минут не парсятся без упоминания. Если в этом есть нужда - жми на кнопку",
                        keyboard=keyboard)
                va = VideoAttachment()
                va.public_download_url = data['download_url']
                if data['start_pos']:
                    tm = TrimVideo()
                    video_content = tm.trim(va, data['start_pos'], data['end_pos'])
                    va = self.bot.get_video_attachment(video_content, peer_id=self.event.peer_id)
                else:
                    va.download_content()
                text = data['title']
        finally:
            self.bot.stop_activity_thread()
        return [va], text

    def get_youtube_audio(self, url) -> (list, str):
        ytm_api = YoutubeMusic()
        data = ytm_api.get_info(url)
        title = f"{data['artists']} - {data['title']}"
        audio_att = self.bot.get_audio_attachment(
            data['content'],
            peer_id=self.event.peer_id,
            filename=f"{title}.{data['format']}",
            thumb=data['cover_url'],
            artist=data['artists'],
            title=data['title']
        )
        return [audio_att], ""

    @retry(3, Exception, sleep_time=2)
    def get_tiktok_video(self, url) -> (list, str):
        ttd_api = TikTok()
        try:
            video_url = ttd_api.get_video_url(url)
        except PWarning as e:
            button = self.bot.get_button("Повторить", command=self.name, args=[url])
            keyboard = self.bot.get_inline_keyboard([button])
            raise PWarning(e.msg, keyboard=keyboard)
        va = VideoAttachment()
        va.public_download_url = video_url
        return [va], None

    def get_reddit_content(self, url) -> (list, str):
        rs = Reddit()
        reddit_data = rs.get_post_data(url)
        if rs.is_gif:
            attachments = [self.bot.get_gif_attachment(reddit_data, peer_id=self.event.peer_id, filename=rs.filename)]
        elif rs.is_image or rs.is_images or rs.is_gallery:
            attachments = [self.bot.get_photo_attachment(att, peer_id=self.event.peer_id, filename=rs.filename) for att
                           in reddit_data]
        elif rs.is_video:
            attachments = [self.bot.get_video_attachment(reddit_data, peer_id=self.event.peer_id, filename=rs.filename)]

        elif rs.is_text or rs.is_link:
            text = reddit_data
            all_photos = []
            text = text \
                .replace("&#x200B;", "") \
                .replace("&amp;#x200B;", "") \
                .replace("&amp;", "&") \
                .replace(" ", " ") \
                .strip()
            text = markdown_to_html(text, self.bot)
            regexps_with_static = ((r"https.*player", "Видео"), (r"https://preview\.redd\.it/.*", "Фото"))
            for regexp, _text in regexps_with_static:
                p = re.compile(regexp)
                for item in reversed(list(p.finditer(text))):
                    start_pos = item.start()
                    end_pos = item.end()
                    if text[start_pos - 9:start_pos] == "<a href=\"":
                        continue
                    link = text[start_pos:end_pos]
                    tg_url = self.bot.get_formatted_url(_text, link)
                    text = text[:start_pos] + tg_url + text[end_pos:]
                    if _text == "Фото":
                        all_photos.append(link)
            all_photos = reversed(all_photos)
            attachments = [self.bot.get_photo_attachment(photo, peer_id=self.event.peer_id, filename=rs.filename)
                           for photo in all_photos]
            return attachments, f"{rs.title}\n\n{text}"
        else:
            raise PWarning("Я хз чё за контент")
        return attachments, rs.title

    def get_instagram_attachment(self, url) -> (list, str):
        try:
            self.check_sender(Role.TRUSTED)
        except PWarning:
            raise PWarning("Медиа инстаграмм доступен только для доверенных пользователей")

        i_api = Instagram()
        data: InstagramAPIData = i_api.get_post_data(url)

        attachments = []
        for item in data.items:
            if item.content_type == InstagramAPIDataItem.CONTENT_TYPE_IMAGE:
                attachment = self.bot.get_photo_attachment(item.download_url, peer_id=self.event.peer_id)
            elif item.content_type == InstagramAPIDataItem.CONTENT_TYPE_VIDEO:
                attachment = self.bot.get_video_attachment(item.download_url, peer_id=self.event.peer_id)
            else:
                continue
            attachments.append(attachment)
            # attachment.download_content(use_proxy=True, headers={"Host":urlparse(attachment.public_download_url).hostname})
        return attachments, data.caption

    def get_twitter_content(self, url) -> (list, str):
        try:
            self.check_sender(Role.TRUSTED)
        except PWarning:
            raise PWarning("Медиа твиттер доступен только для доверенных пользователей")

        t_api = Twitter()
        with_threads = self.event.message.keys and self.event.message.keys[0] in ['thread', 'threads', 'with-threads',
                                                                                  'тред', 'треды']
        data = t_api.get_post_data(url, with_threads=with_threads)

        if not data.items:
            return [], data.caption

        attachments = []
        for att in data.items:
            if att.content_type == att.CONTENT_TYPE_VIDEO:
                video = self.bot.get_video_attachment(att.download_url, peer_id=self.event.peer_id)
                attachments.append(video)
            if att.content_type == att.CONTENT_TYPE_IMAGE:
                photo = self.bot.get_photo_attachment(att.download_url, peer_id=self.event.peer_id)
                attachments.append(photo)

        return attachments, data.caption

    def get_pikabu_video(self, url) -> (list, str):
        p_api = Pikabu()
        data = p_api.get_video_data(url)
        video = self.bot.get_video_attachment(data['download_url'], peer_id=self.event.peer_id,
                                              filename=data['filename'])
        return [video], data['title']

    def get_yandex_music(self, url) -> (list, str):
        ym_api = YandexMusicAPI()
        res = ym_api.parse_album_and_track_ids(url)
        if res['album_id'] and not res['track_id']:
            try:
                self.check_sender(Role.TRUSTED)
            except PWarning:
                raise PWarning("Скачивание альбомов Yandex Music доступно только для доверенных пользователей")
            ya = YandexAlbum(res['album_id'])
            ya.set_tracks()
            tracks = ya.tracks
        else:
            yt = YandexTrack(res['track_id'])
            tracks = [yt]

        audios = []
        for track in tracks:
            audiofile = track.download()
            title = f"{track.artists} - {track.title}"
            audio = self.bot.get_audio_attachment(
                audiofile,
                peer_id=self.event.peer_id,
                filename=f"{title}.{track.format}",
                thumb=track.cover_url,
                artist=track.artists,
                title=track.title
            )
            audios.append(audio)
        return audios, ""

    def get_pinterest_attachment(self, url) -> (list, str):
        p_api = Pinterest()
        data: PinterestDataItem = p_api.get_post_data(url)

        if data.content_type == PinterestDataItem.CONTENT_TYPE_VIDEO:
            attachment = self.bot.get_video_attachment(data.download_url, peer_id=self.event.peer_id)
        elif data.content_type == PinterestDataItem.CONTENT_TYPE_IMAGE:
            attachment = self.bot.get_photo_attachment(data.download_url, peer_id=self.event.peer_id)
        elif data.content_type == PinterestDataItem.CONTENT_TYPE_GIF:
            attachment = self.bot.get_gif_attachment(data.download_url, peer_id=self.event.peer_id)
        else:
            raise PWarning(Pinterest.ERROR_MSG)

        return [attachment], data.caption

    def get_coub_video(self, url) -> (list, str):
        headers = get_default_headers()
        content = requests.get(url, headers=headers).content
        bs4 = BeautifulSoup(content, "html.parser")
        data = json.loads(bs4.find("script", {'id': 'coubPageCoubJson'}).text)
        video_url = data['file_versions']['share']['default']
        video = self.bot.get_video_attachment(video_url, peer_id=self.event.peer_id)
        title = data['title']
        return [video], title

    def get_vk_video(self, url) -> (list, str):
        vk_api = VKVideo()
        r = re.findall(r'\?(list=.*)', url)
        if r:
            url = url.replace(r[0], "")
            url = url.rstrip("?")
        video_info = vk_api.get_video_info(url)

        if not video_info:
            raise PWarning("Не получилось распарсить ссылку")

        title = video_info['video_title']

        try:
            cache = VideoCache.objects.get(channel_id=video_info['channel_id'], video_id=video_info['video_id'])
        except VideoCache.DoesNotExist:
            try:
                self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
                video = vk_api.get_video(url)
            finally:
                self.bot.stop_activity_thread()

            filename = f"{video_info['channel_title']}_{title}"
            cache = self._save_video_to_media_cache(
                video_info['channel_id'],
                video_info['video_id'],
                filename,
                video
            )
        filesize_mb = len(cache.video) / 1024 / 1024
        attachments = []
        if filesize_mb < self.bot.MAX_VIDEO_SIZE_MB:
            attachments = [self.bot.get_video_attachment(cache.video, peer_id=self.event.peer_id)]
        msg = f"{title}\nCкачать можно здесь {self.bot.get_formatted_url('здесь', MAIN_SITE + cache.video.url)}"
        return attachments, msg

    def get_scope_gg_video(self, url) -> (list, str):
        content = requests.get(url).content
        bs4 = BeautifulSoup(content, "html.parser")
        data = json.loads(bs4.select_one('#__NEXT_DATA__').text)
        clip_id = data['query']['clipId']
        clip = data['props']['initialState']['publicDashboard']['allStars']['clip']
        snapshot_url = clip['clipSnapshotURL']
        clip_length = clip['clipLength'] - 0.3
        first_id = snapshot_url.replace('https://media.allstar.gg/', '').split('/', 1)[0]
        url = f"https://media.allstar.gg/{first_id}/clips/{clip_id}.mp4"

        video = self.bot.get_video_attachment(url, peer_id=self.event.peer_id)
        vh = VideoHandler(video)
        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
            trimmed_video = vh.trim(0, clip_length)
        finally:
            self.bot.stop_activity_thread()

        video = self.bot.get_video_attachment(trimmed_video, peer_id=self.event.peer_id)
        return [video], None

    def get_clips_twitch_video(self, url) -> (list, str):
        slug = url.split(CLIPS_TWITCH_URLS[0], 1)[-1].lstrip('/')
        clip_info = twitch.get_clip(slug)
        title = clip_info['title']
        video_url = get_clip_authenticated_url(slug, "source")
        video = self.bot.get_video_attachment(video_url, peer_id=self.event.peer_id)
        video.download_content()
        return [video], title

    def get_facebook_video(self, url) -> (list, str):
        f_api = Facebook()
        data = f_api.get_video_info(url)

        video = self.bot.get_video_attachment(data['download_url'], peer_id=self.event.peer_id)
        return [video], data['caption']

    def get_premiere_video(self, url) -> (list, str):
        p_api = Premier()
        data = p_api.parse_video(url)

        try:
            cache = VideoCache.objects.get(channel_id=data['show_id'], video_id=data['video_id'])
        except VideoCache.DoesNotExist:
            try:
                self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
                video = p_api.download_video(url, data['video_id'])
            finally:
                self.bot.stop_activity_thread()

            cache = self._save_video_to_media_cache(
                data['show_id'],
                data['video_id'],
                data['filename'],
                video
            )
        filesize_mb = len(cache.video) / 1024 / 1024
        attachments = []
        if filesize_mb < self.bot.MAX_VIDEO_SIZE_MB:
            attachments = [self.bot.get_video_attachment(cache.video, peer_id=self.event.peer_id)]
        msg = f"{data['title']}\nCкачать можно здесь {self.bot.get_formatted_url('здесь', MAIN_SITE + cache.video.url)}"
        return attachments, msg

    def get_spotify_music(self, url):

        track_id = re.findall(r'track\/(\w*)', url)[0]

        s = Spotify()
        data = s.get_info(track_id)

        title = f"{data['artists']} - {data['title']}"
        audio_att = self.bot.get_audio_attachment(
            data['content'],
            peer_id=self.event.peer_id,
            filename=f"{title}.{data['format']}",
            thumb=data['cover_url'],
            artist=data['artists'],
            title=data['title']
        )
        return [audio_att], ""

    @staticmethod
    def _save_video_to_media_cache(channel_id: str, video_id: str, name: str, content: bytes):
        filename = f"{name}.mp4"
        cache = VideoCache(
            channel_id=channel_id,
            video_id=video_id,
            filename=filename
        )
        cache.video.save(filename, content=BytesIO(content))
        cache.save()
        return cache
