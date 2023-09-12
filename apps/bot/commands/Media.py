import json
import re
from io import BytesIO
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from twitchdl import twitch
from twitchdl.commands.download import get_clip_authenticated_url

from apps.bot.APIs.FacebookVideoAPI import FacebookVideoAPI
from apps.bot.APIs.InstagramAPI import InstagramAPI
from apps.bot.APIs.PikabuAPI import PikabuAPI
from apps.bot.APIs.PinterestAPI import PinterestAPI
from apps.bot.APIs.TheHoleAPI import TheHoleAPI
from apps.bot.APIs.TikTokDownloaderAPI import TikTokDownloaderAPI
from apps.bot.APIs.TwitterAPI import TwitterAPI
from apps.bot.APIs.VKVideoAPI import VKVideoAPI
from apps.bot.APIs.WASDAPI import WASDAPI
from apps.bot.APIs.YandexMusicAPI import YandexMusicAPI
from apps.bot.APIs.YoutubeMusicAPI import YoutubeMusicAPI
from apps.bot.APIs.YoutubeVideoAPI import YoutubeVideoAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.bots.tg.TgBot import TgBot
from apps.bot.classes.consts.ActivitiesEnum import ActivitiesEnum
from apps.bot.classes.consts.Consts import Platform, Role
from apps.bot.classes.consts.Exceptions import PWarning, PSkip
from apps.bot.classes.events.Event import Event
from apps.bot.classes.messages.ResponseMessage import ResponseMessage, ResponseMessageItem
from apps.bot.classes.messages.attachments.LinkAttachment import LinkAttachment
from apps.bot.commands.TrimVideo import TrimVideo
from apps.bot.utils.RedditSaver import RedditSaver
from apps.bot.utils.VideoTrimmer import VideoTrimmer
from apps.bot.utils.utils import get_urls_from_text, replace_markdown_links, replace_markdown_bolds, \
    replace_markdown_quotes
from apps.service.models import VideoCache
from petrovich.settings import MAIN_SITE

YOUTUBE_URLS = ('www.youtube.com', 'youtube.com', "www.youtu.be", "youtu.be", "m.youtube.com")
YOUTUBE_MUSIC_URLS = ("music.youtube.com",)
REDDIT_URLS = ("www.reddit.com", "reddit.com")
TIKTOK_URLS = ("www.tiktok.com", 'vm.tiktok.com', 'm.tiktok.com', 'vt.tiktok.com')
INSTAGRAM_URLS = ('www.instagram.com', 'instagram.com')
TWITTER_URLS = ('www.twitter.com', 'twitter.com', 'x.com')
PIKABU_URLS = ('www.pikabu.ru', 'pikabu.ru')
THE_HOLE_URLS = ('www.the-hole.tv', 'the-hole.tv')
WASD_URLS = ('www.wasd.tv', 'wasd.tv')
YANDEX_MUSIC_URLS = ('music.yandex.ru',)
PINTEREST_URLS = ('pinterest.com', 'ru.pinterest.com', 'www.pinterest.com', 'pin.it')
COUB_URLS = ('coub.com',)
VK_URLS = ('vk.com',)
SCOPE_GG_URLS = ('app.scope.gg',)
CLIPS_TWITCH_URLS = ('clips.twitch.tv',)
FACEBOOK_URLS = ('www.facebook.com', 'facebook.com', 'fb.watch')

MEDIA_URLS = tuple(
    list(YOUTUBE_URLS) +
    list(YOUTUBE_MUSIC_URLS) +
    list(REDDIT_URLS) +
    list(TIKTOK_URLS) +
    list(INSTAGRAM_URLS) +
    list(TWITTER_URLS) +
    list(PIKABU_URLS) +
    list(THE_HOLE_URLS) +
    list(WASD_URLS) +
    list(YANDEX_MUSIC_URLS) +
    list(PINTEREST_URLS) +
    list(COUB_URLS) +
    list(VK_URLS) +
    list(SCOPE_GG_URLS) +
    list(CLIPS_TWITCH_URLS) +
    list(FACEBOOK_URLS)
)


class Media(Command):
    name = "медиа"
    names = ["media"]
    help_text = "скачивает видео из соцсетей и присылает его"
    help_texts = ["(ссылка на видео/пост) - скачивает видео из соцсетей и присылает его"]
    help_texts_extra = "Поддерживаемые соцсети: Youtube/Youtube Music/Reddit/TikTok/Instagram/Twitter/Pikabu/" \
                       "The Hole/WASD/Yandex Music/Pinterest/Coub/VK Video/ScopeGG/TwitchClips/Facebook video\n\n" \
                       "Ключ --nomedia позволяет не запускать команду\n" \
                       "Ключ --audio позволяет скачивать аудиодорожку для видео с ютуба\n\n" \
                       "Видосы из ютуба качаются автоматически только если длина ролика < 2 минут. \n" \
                       "Вручную с указанием команды - скачается"
    platforms = [Platform.TG]
    attachments = [LinkAttachment]

    bot: TgBot

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_command_name = None

    @staticmethod
    def accept_extra(event: Event) -> bool:
        if event.message and not event.message.mentioned:
            if "nomedia" in event.message.keys:
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

        chosen_url_pos = source.find(chosen_url)

        answer = ""
        if title:
            answer = f"{title}\n"
        if self.event.is_from_chat:
            answer += f"\nОт {self.event.sender}"

        source_hostname = str(urlparse(chosen_url).hostname).lstrip('www.')
        if len(attachments) == 1:
            answer += f'\nИсточник: {self.bot.get_formatted_url(source_hostname, chosen_url)}'
        else:
            answer += f'\nИсточник: {chosen_url}'

        # Костыль, чтобы видосы которые шарятся с мобилы с реддита не дублировали title

        extra_text = source[:chosen_url_pos].strip() + "\n" + source[chosen_url_pos + len(chosen_url):].strip()
        for key in self.event.message.keys:
            extra_text = extra_text.replace(self.event.message.KEYS_STR + key, "")
            extra_text = extra_text.replace(self.event.message.KEYS_SYMBOL + key, "")
        extra_text = extra_text.strip()
        if extra_text and extra_text != title:
            answer += f"\n\n{extra_text}"

        reply_to = None
        if self.event.fwd:
            reply_to = self.event.fwd[0].message.id

        rmi = ResponseMessageItem(text=answer, attachments=attachments, reply_to=reply_to, peer_id=self.event.peer_id,
                                  message_thread_id=self.event.message_thread_id)
        res = self.bot.send_response_message_item(rmi)
        if res.json()['ok']:
            self.bot.delete_message(self.event.peer_id, self.event.message.id)

    def get_method_and_chosen_url(self, source):
        MEDIA_TRANSLATOR = {
            YOUTUBE_URLS: self.get_youtube_video,
            YOUTUBE_MUSIC_URLS: self.get_youtube_audio,
            TIKTOK_URLS: self.get_tiktok_video,
            REDDIT_URLS: self.get_reddit_attachment,
            INSTAGRAM_URLS: self.get_instagram_attachment,
            TWITTER_URLS: self.get_twitter_video,
            PIKABU_URLS: self.get_pikabu_video,
            THE_HOLE_URLS: self.get_the_hole_video,
            WASD_URLS: self.get_wasd_video,
            YANDEX_MUSIC_URLS: self.get_yandex_music,
            PINTEREST_URLS: self.get_pinterest_attachment,
            COUB_URLS: self.get_coub_video,
            VK_URLS: self.get_vk_video,
            SCOPE_GG_URLS: self.get_scope_gg_video,
            CLIPS_TWITCH_URLS: self.get_clips_twitch_video,
            FACEBOOK_URLS: self.get_facebook_video,
        }

        urls = get_urls_from_text(source)
        for url in urls:
            hostname = urlparse(url).hostname
            if not hostname:
                raise PWarning("Не нашёл ссылки")
            for k in MEDIA_TRANSLATOR:
                if hostname in k:
                    return MEDIA_TRANSLATOR[k], url

        raise PWarning("Не медиа ссылка")

    def get_youtube_video(self, url) -> (list, str):
        if 'audio' in self.event.message.keys:
            return self.get_youtube_audio(url)
        y_api = YoutubeVideoAPI(max_filesize_mb=self.bot.MAX_VIDEO_SIZE_MB)

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
            else:
                content_url = y_api.get_download_url(url)
                if not self.has_command_name and y_api.duration > 120:
                    button = self.bot.get_button(f"{self.event.message.COMMAND_SYMBOLS[0]}{self.name} {url}")
                    keyboard = self.bot.get_inline_keyboard([button])
                    raise PWarning(
                        "Видосы до 2х минут не парсятся без упоминания. Если в этом есть нужда - жми на кнопку",
                        keyboard=keyboard)
                video_content = requests.get(content_url).content
        finally:
            self.bot.stop_activity_thread()
        video = self.bot.get_video_attachment(video_content, peer_id=self.event.peer_id, filename=y_api.filename)

        text = y_api.title
        return [video], text

    def get_youtube_audio(self, url) -> (list, str):
        track = YoutubeMusicAPI(url)
        track.get_info()
        title = f"{track.artists} - {track.title}"
        audio_att = self.bot.get_audio_attachment(track.content, peer_id=self.event.peer_id,
                                                  filename=f"{title}.{track.format}",
                                                  thumb=track.cover_url, artist=track.artists, title=track.title)
        return [audio_att], ""

    def get_tiktok_video(self, url) -> (list, str):
        ttd_api = TikTokDownloaderAPI()
        video_url = ttd_api.get_video_url(url)
        video_content = requests.get(video_url).content

        video = self.bot.get_video_attachment(video_content, peer_id=self.event.peer_id, filename="tiktok.mp4")
        return [video], None

    def get_reddit_attachment(self, url) -> (list, str):
        rs = RedditSaver()
        reddit_data = rs.get_from_reddit(url)
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
            text = text.replace("&#x200B;", "").replace("&amp;#x200B;", "").replace("&amp;", "&").replace(" ",
                                                                                                          " ").strip()
            text = replace_markdown_links(text, self.bot)

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
            text = replace_markdown_bolds(text, self.bot)
            text = replace_markdown_quotes(text, self.bot)

            if all_photos:
                atatchments = [self.bot.get_photo_attachment(x, filename=rs.filename) for x in all_photos]
                rmi = ResponseMessageItem(attachments=atatchments, peer_id=self.event.peer_id,
                                          message_thread_id=self.event.message_thread_id)
                self.bot.send_response_message_item(rmi)
            return [], f"{rs.title}\n\n{text}"
        else:
            raise PWarning("Я хз чё за контент")
        return attachments, rs.title

    def get_instagram_attachment(self, url) -> (list, str):
        try:
            self.check_sender(Role.TRUSTED)
        except PWarning:
            raise PWarning("медиа инстаграмм доступен только для доверенных пользователей")

        i_api = InstagramAPI()
        content_url = i_api.get_content_url(url)

        if i_api.content_type == i_api.CONTENT_TYPE_IMAGE:
            attachment = self.bot.get_photo_attachment(content_url, peer_id=self.event.peer_id)
        elif i_api.content_type == i_api.CONTENT_TYPE_VIDEO:
            attachment = self.bot.get_video_attachment(content_url, peer_id=self.event.peer_id)
        else:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")
        return [attachment], i_api.caption

    def get_twitter_video(self, url) -> (list, str):
        try:
            self.check_sender(Role.TRUSTED)
        except PWarning:
            raise PWarning("медиа твиттер доступен только для доверенных пользователей")

        t_api = TwitterAPI()
        content_url = t_api.get_content_url(url)

        if t_api.content_type == t_api.CONTENT_TYPE_IMAGE:
            if isinstance(content_url, list):
                attachments = [self.bot.get_photo_attachment(image_url, peer_id=self.event.peer_id) for image_url in
                               content_url]
            else:
                attachments = [self.bot.get_photo_attachment(content_url, peer_id=self.event.peer_id)]
            return attachments, t_api.caption
        elif t_api.content_type == t_api.CONTENT_TYPE_VIDEO:
            video = self.bot.get_video_attachment(content_url, peer_id=self.event.peer_id)
            return [video], t_api.caption
        elif t_api.content_type == t_api.CONTENT_TYPE_TEXT:
            return [], t_api.caption
        else:
            raise PWarning("Ссылка на твит не является видео/фото/текстом")

    def get_pikabu_video(self, url) -> (list, str):
        p_api = PikabuAPI()
        webm = p_api.get_video_url_from_post(url)
        video_content = requests.get(webm).content
        video = self.bot.get_video_attachment(video_content, peer_id=self.event.peer_id, filename=p_api.filename)
        return [video], p_api.title

    def get_the_hole_video(self, url) -> (list, str):
        the_hole_api = TheHoleAPI()
        the_hole_api.parse_video(url)
        title = the_hole_api.video_title

        try:
            cache = VideoCache.objects.get(channel_id=the_hole_api.channel_id, video_id=the_hole_api.video_id)
        except VideoCache.DoesNotExist:
            try:
                self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
                video = the_hole_api.get_video(url)
            finally:
                self.bot.stop_activity_thread()

            filename = f"{the_hole_api.channel_title}_{the_hole_api.video_title}"

            cache = self._save_video_to_media_cache(
                the_hole_api.channel_id,
                the_hole_api.video_id,
                filename,
                video
            )

        filesize_mb = len(cache.video) / 1024 / 1024
        attachments = []
        if filesize_mb < self.bot.MAX_VIDEO_SIZE_MB:
            attachments = [self.bot.get_video_attachment(cache.video, peer_id=self.event.peer_id)]
        msg = title + f"\nCкачать можно здесь {self.bot.get_formatted_url('здесь', MAIN_SITE + cache.video.url)}"
        return attachments, msg

    def get_wasd_video(self, url) -> (list, str):
        wasd_api = WASDAPI()
        wasd_api.parse_video_m3u8(url)
        file = self.bot.get_document_attachment(
            wasd_api.m3u8_bytes,
            peer_id=self.event.peer_id,
            filename=f"{wasd_api.title} - {wasd_api.show_name} | WASD.m3u8"
        )
        return [file], f"{wasd_api.title} | {wasd_api.show_name}"

    def get_yandex_music(self, url) -> (list, str):
        track = YandexMusicAPI(url)
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
        return [audio], ""

    def get_pinterest_attachment(self, url) -> (list, str):
        p_api = PinterestAPI(url)
        content = p_api.get_attachment()
        if p_api.is_video:
            attachment = self.bot.get_video_attachment(content, peer_id=self.event.peer_id, filename=p_api.filename)
        elif p_api.is_image:
            attachment = self.bot.get_photo_attachment(content, peer_id=self.event.peer_id, filename=p_api.filename)
        elif p_api.is_gif:
            attachment = self.bot.get_gif_attachment(content, peer_id=self.event.peer_id, filename=p_api.filename)
        else:
            raise PWarning("Я хз чё за контент")

        return [attachment], p_api.title

    def get_coub_video(self, url) -> (list, str):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        content = requests.get(url, headers=headers).content
        bs4 = BeautifulSoup(content, "html.parser")
        data = json.loads(bs4.find("script", {'id': 'coubPageCoubJson'}).text)
        video_url = data['file_versions']['share']['default']
        video = self.bot.get_video_attachment(video_url, peer_id=self.event.peer_id)
        title = data['title']
        return [video], title

    def get_vk_video(self, url) -> (list, str):
        vk_v_api = VKVideoAPI()
        video_info = vk_v_api.get_video_info(url)

        if not video_info and not self.has_command_name > 120:
            raise PSkip()

        title = video_info['video_title']

        try:
            cache = VideoCache.objects.get(channel_id=video_info['channel_id'], video_id=video_info['video_id'])
        except VideoCache.DoesNotExist:
            try:
                self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
                video = vk_v_api.get_video(url)
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
        msg = title + f"\nCкачать можно здесь {self.bot.get_formatted_url('здесь', MAIN_SITE + cache.video.url)}"
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

        # video_content = requests.get(webm).content
        video = self.bot.get_video_attachment(url, peer_id=self.event.peer_id)
        vt = VideoTrimmer()
        try:
            self.bot.set_activity_thread(self.event.peer_id, ActivitiesEnum.UPLOAD_VIDEO)
            trimmed_video = vt.trim(video.download_content(), 0, clip_length)
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
        video.public_download_url = None
        return [video], title

    def get_facebook_video(self, url) -> (list, str):
        f_api = FacebookVideoAPI()
        content_url = f_api.get_content_url(url)

        video = self.bot.get_video_attachment(content_url, peer_id=self.event.peer_id)
        # raise PWarning("Ссылка на фейсбук не является видео/фото")
        return [video], f_api.caption

    @staticmethod
    def _save_video_to_media_cache(channel_id, video_id, name, content):
        filename = f"{name}.mp4"
        cache = VideoCache(
            channel_id=channel_id,
            video_id=video_id,
            filename=filename
        )
        cache.video.save(filename, content=BytesIO(content))
        cache.save()
        return cache
