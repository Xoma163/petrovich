import re
from urllib.parse import urlparse

import requests
import youtube_dl
from urllib3.exceptions import MaxRetryError

from apps.bot.APIs.InstagramAPI import InstagramAPI
from apps.bot.APIs.PikabuAPI import PikabuAPI
from apps.bot.APIs.RedditSaver import RedditSaver
from apps.bot.APIs.TheHoleAPI import TheHoleAPI
from apps.bot.APIs.TikTokDownloaderAPI import TikTokDownloaderAPI
from apps.bot.APIs.WASDAPI import WASDAPI
from apps.bot.APIs.YandexMusicAPI import YandexMusicAPI
from apps.bot.APIs.YoutubeAPI import YoutubeAPI
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning, PSkip
from apps.bot.utils.NothingLogger import NothingLogger
from apps.bot.utils.utils import get_urls_from_text, get_tg_formatted_url, get_tg_bold_text, get_tg_formatted_text_line

YOUTUBE_URLS = ('www.youtube.com', 'youtube.com', "www.youtu.be", "youtu.be")
REDDIT_URLS = ("www.reddit.com",)
TIKTOK_URLS = ("www.tiktok.com", 'vm.tiktok.com', 'm.tiktok.com', 'vt.tiktok.com')
INSTAGRAM_URLS = ('www.instagram.com', 'instagram.com')
TWITTER_URLS = ('www.twitter.com', 'twitter.com')
PIKABU_URLS = ('www.pikabu.ru', 'pikabu.ru')
THE_HOLE_URLS = ('www.the-hole.tv', 'the-hole.tv')
WASD_URLS = ('www.wasd.tv', 'wasd.tv')
YANDEX_MUSIC_URLS = ('music.yandex.ru',)

MEDIA_URLS = tuple(
    list(YOUTUBE_URLS) +
    list(REDDIT_URLS) +
    list(TIKTOK_URLS) +
    list(INSTAGRAM_URLS) +
    list(TWITTER_URLS) +
    list(PIKABU_URLS) +
    list(THE_HOLE_URLS) +
    list(WASD_URLS) +
    list(YANDEX_MUSIC_URLS)
)


class Media(Command):
    name = "медиа"
    help_text = "скачивает видео из соцсетей и присылает его"
    help_texts = ["(ссылка на видео) - скачивает видео из соцсетей и присылает его"]
    help_texts_extra = "Поддерживаемые соцсети: Reddit/TikTok/YouTube/Instagram/Twitter/Pikabu/TheHole"
    platforms = [Platform.TG]

    @staticmethod
    def accept_extra(event):
        if event.message and not event.message.mentioned:
            all_urls = get_urls_from_text(event.message.clear_case)
            has_fwd_with_message = event.fwd and event.fwd[0].message and event.fwd[0].message.clear_case
            if event.is_from_pm and has_fwd_with_message:
                all_urls += get_urls_from_text(event.fwd[0].message.clear_case)
            for url in all_urls:
                message_is_media_link = urlparse(url).hostname in MEDIA_URLS
                if message_is_media_link:
                    return True
        return False

    def start(self):
        if self.event.message.command in self.full_names:
            if self.event.message.args:
                source = self.event.message.args_case[0]
            elif self.event.fwd:
                source = self.event.fwd[0].message.raw
            else:
                raise PWarning("Для работы команды требуются аргументы или пересылаемые сообщения")
            has_command_name = True
        else:
            source = self.event.message.raw
            has_command_name = False

        method, chosen_url = self.get_method_and_chosen_url(source)

        try:
            attachments, title = method(chosen_url)
        except PWarning as e:
            # Если была вызвана команда или отправлено сообщение в лс
            if has_command_name or self.event.is_from_pm:
                raise e
            else:
                raise PSkip()

        chosen_url_pos = source.find(chosen_url)
        extra_text = source[:chosen_url_pos].strip() + "\n" + source[chosen_url_pos + len(chosen_url):].strip()
        extra_text = extra_text.strip()

        text = ""
        if title:
            text = f"{title}\n"
        text += f"\nОт пользователя {self.event.sender}"

        if self.event.platform == Platform.TG:
            source_hostname = str(urlparse(chosen_url).hostname).lstrip('www.')
            text += f'\nИсточник: {get_tg_formatted_url(source_hostname, chosen_url)}'
        else:
            text += f"\n{chosen_url}"
        # Костыль, чтобы видосы которые шарятся с мобилы с реддита не дублировали title
        if extra_text and extra_text != title:
            text += f"\n\n{extra_text}"

        reply_to = None
        if self.event.fwd:
            reply_to = self.event.fwd[0].message.id

        res = self.bot.parse_and_send_msgs({'text': text, 'attachments': attachments, 'reply_to': reply_to},
                                           self.event.peer_id, self.event.message_thread_id)
        if res[0]['success']:
            self.bot.delete_message(self.event.peer_id, self.event.message.id)

    def get_method_and_chosen_url(self, source):
        MEDIA_TRANSLATOR = {
            YOUTUBE_URLS: self.get_youtube_video,
            TIKTOK_URLS: self.get_tiktok_video,
            REDDIT_URLS: self.get_reddit_attachment,
            INSTAGRAM_URLS: self.get_instagram_attachment,
            TWITTER_URLS: self.get_twitter_video,
            PIKABU_URLS: self.get_pikabu_video,
            THE_HOLE_URLS: self.get_the_hole_video,
            WASD_URLS: self.get_wasd_video,
            YANDEX_MUSIC_URLS: self.get_yandex_music,
        }

        method = None
        urls = get_urls_from_text(source)
        for url in urls:
            hostname = urlparse(url).hostname
            if not hostname:
                raise PWarning("Не нашёл ссылки")
            for k in MEDIA_TRANSLATOR:
                if hostname in k:
                    return MEDIA_TRANSLATOR[k], url

        if not method:
            raise PWarning("Не youtube/tiktok/reddit/instagram ссылка")

    def get_youtube_video(self, url):
        y_api = YoutubeAPI()
        timecode = y_api.get_timecode_str(url)
        content_url = y_api.get_video_download_url(url, self.event.platform)
        video_content = requests.get(content_url).content
        attachments = [self.bot.upload_video(video_content, peer_id=self.event.peer_id)]

        text = y_api.title
        if timecode:
            text = f"{text}\n\n{timecode}"
        return attachments, text

    def get_tiktok_video(self, url):
        ttd_api = TikTokDownloaderAPI()
        video_url = ttd_api.get_video_url(url)
        video = requests.get(video_url).content

        attachments = [self.bot.upload_video(video, peer_id=self.event.peer_id)]
        return attachments, None

    def get_reddit_attachment(self, url):
        rs = RedditSaver()
        attachment = rs.get_from_reddit(url)
        if rs.is_gif:
            attachments = self.bot.upload_gif(attachment)
        elif rs.is_image or rs.is_images or rs.is_gallery:
            attachments = self.bot.upload_photos(attachment, peer_id=self.event.peer_id)
        elif rs.is_video:
            attachments = self.bot.upload_video(attachment, peer_id=self.event.peer_id)

        elif rs.is_text or rs.is_link:
            text = attachment
            all_photos = []
            if self.event.platform == Platform.TG:
                text = text.replace("&#x200B;", "").replace("&amp;#x200B;", "").replace("&amp;", "&").replace(" ",
                                                                                                              " ").strip()
                p = re.compile(r"\[(.*)\]\(([^\)]*)\)")  # markdown links
                for item in reversed(list(p.finditer(text))):
                    start_pos = item.start()
                    end_pos = item.end()
                    link_text = text[item.regs[1][0]:item.regs[1][1]]
                    link = text[item.regs[2][0]:item.regs[2][1]]
                    tg_url = get_tg_formatted_url(link_text, link)
                    text = text[:start_pos] + tg_url + text[end_pos:]

                regexps_with_static = ((r"https.*player", "Видео"), (r"https://preview\.redd\.it/.*", "Фото"))
                for regexp, _text in regexps_with_static:
                    p = re.compile(regexp)
                    for item in reversed(list(p.finditer(text))):
                        start_pos = item.start()
                        end_pos = item.end()
                        if text[start_pos - 9:start_pos] == "<a href=\"":
                            continue
                        link = text[start_pos:end_pos]
                        tg_url = get_tg_formatted_url(_text, link)
                        text = text[:start_pos] + tg_url + text[end_pos:]
                        if _text == "Фото":
                            all_photos.append(link)
                p = re.compile(r'\*\*(.*)\*\*')  # markdown bold
                for item in reversed(list(p.finditer(text))):
                    start_pos = item.start()
                    end_pos = item.end()
                    bold_text = text[item.regs[1][0]:item.regs[1][1]]
                    tg_bold_text = get_tg_bold_text(bold_text).replace("**", '')
                    text = text[:start_pos] + tg_bold_text + text[end_pos:]

                p = re.compile(r'&gt;(.*)\n')  # markdown quote
                for item in reversed(list(p.finditer(text))):
                    start_pos = item.start()
                    end_pos = item.end()
                    quote_text = text[item.regs[1][0]:item.regs[1][1]]
                    tg_quote_text = get_tg_formatted_text_line(quote_text)
                    text = text[:start_pos] + tg_quote_text + text[end_pos:]
            if all_photos:
                msg = {'attachments': self.bot.upload_photos(all_photos)}
                self.bot.parse_and_send_msgs(msg, self.event.peer_id, self.event.message_thread_id)
            return [], f"{rs.title}\n\n{text}"
        else:
            raise PWarning("Я хз чё за контент")
        return attachments, rs.title

    def get_instagram_attachment(self, url):
        i_api = InstagramAPI()
        try:
            content_url = i_api.get_content_url(url)
        except (MaxRetryError, requests.exceptions.ConnectionError):
            raise PWarning("Инста забанена :(")

        if i_api.content_type == i_api.CONTENT_TYPE_IMAGE:
            return self.bot.upload_photo([content_url], peer_id=self.event.peer_id), ""
        elif i_api.content_type in [i_api.CONTENT_TYPE_VIDEO, i_api.CONTENT_TYPE_REEL]:
            return self.bot.upload_video(content_url, peer_id=self.event.peer_id), ""

    def get_twitter_video(self, url):
        ydl_params = {
            'outtmpl': '%(id)s%(ext)s',
            'logger': NothingLogger()
        }
        ydl = youtube_dl.YoutubeDL(ydl_params)
        ydl.add_default_info_extractors()

        try:
            video_info = ydl.extract_info(url, download=False)
        except youtube_dl.utils.DownloadError:
            raise PWarning("Не смог найти видео по этой ссылке")
        video_url = video_info['url']
        video_content = requests.get(video_url).content
        attachments = [self.bot.upload_video(video_content, peer_id=self.event.peer_id)]
        return attachments, video_info['title']

    def get_pikabu_video(self, url):
        p_api = PikabuAPI()
        webm = p_api.get_video_url_from_post(url)
        video_content = requests.get(webm).content
        attachments = [self.bot.upload_video(video_content, peer_id=self.event.peer_id)]
        return attachments, p_api.title

    def get_the_hole_video(self, url):
        the_hole_api = TheHoleAPI()
        the_hole_api.parse_video(url)
        attachments = [self.bot.upload_document(the_hole_api.m3u8_bytes, peer_id=self.event.peer_id,
                                                filename=f"{the_hole_api.title} - {the_hole_api.show_name} | The Hole.m3u8")]
        return attachments, f"{the_hole_api.title} | {the_hole_api.show_name}"

    def get_wasd_video(self, url):
        wasd_api = WASDAPI()
        wasd_api.parse_video_m3u8(url)
        attachments = [self.bot.upload_document(wasd_api.m3u8_bytes, peer_id=self.event.peer_id,
                                                filename=f"{wasd_api.title} - {wasd_api.show_name} | WASD.m3u8")]
        return attachments, f"{wasd_api.title} | {wasd_api.show_name}"

    def get_yandex_music(self, url):
        track = YandexMusicAPI(url)
        audiofile = track.download_track()
        cover = track.cover_url
        title = f"{track.artists} - {track.title}"
        audio_att = self.bot.upload_audio(audiofile, peer_id=self.event.peer_id, filename=f"{title}.{track.format}",
                                          title=title)
        cover_att = self.bot.upload_photo(cover, guarantee_url=True)
        if cover_att:
            msg = {'attachments': cover_att}
            self.bot.parse_and_send_msgs(msg, self.event.peer_id, self.event.message_thread_id)
        attachments = [audio_att]
        return attachments, title
