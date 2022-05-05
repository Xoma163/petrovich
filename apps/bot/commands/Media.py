import json
import re
from urllib.parse import urlparse

import requests
import youtube_dl
from bs4 import BeautifulSoup

from apps.bot.APIs.RedditVideoDownloader import RedditSaver
from apps.bot.classes.Command import Command
from apps.bot.classes.consts.Consts import Platform
from apps.bot.classes.consts.Exceptions import PWarning, PSkip
from apps.bot.utils.utils import get_urls_from_text, get_tg_formatted_url

YOUTUBE_URLS = ('www.youtube.com', 'youtube.com', "www.youtu.be", "youtu.be")
REDDIT_URLS = ("www.reddit.com",)
TIKTOK_URLS = ("www.tiktok.com", 'vm.tiktok.com', 'm.tiktok.com', 'vt.tiktok.com')
INSTAGRAM_URLS = ('www.instagram.com', 'instagram.com')
TWITTER_URLS = ('www.twitter.com', 'twitter.com')
PIKABU_URLS = ('www.pikabu.ru', 'pikabu.ru')

MEDIA_URLS = tuple(
    list(YOUTUBE_URLS) +
    list(REDDIT_URLS) +
    list(TIKTOK_URLS) +
    list(INSTAGRAM_URLS) +
    list(TWITTER_URLS) +
    list(PIKABU_URLS)
)


class Media(Command):
    name = "медиа"
    help_text = "скачивает видео из Reddit/TikTok/YouTube/Instagram и присылает его"
    help_texts = [
        "(ссылка на видео) - скачивает видео из Reddit/TikTok/YouTube/Instagram и присылает его"
    ]
    platforms = [Platform.TG]

    def __init__(self):
        super().__init__()
        self.MEDIA_TRANSLATOR = {
            YOUTUBE_URLS: self.get_youtube_video,
            TIKTOK_URLS: self.get_tiktok_video,
            REDDIT_URLS: self.get_reddit_attachment,
            INSTAGRAM_URLS: self.get_instagram_attachment,
            TWITTER_URLS: self.get_twitter_video,
            PIKABU_URLS: self.get_pikabu_video,
        }

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

        if has_command_name or self.event.is_from_pm:
            return {'attachments': attachments}
        else:

            chosen_url_pos = source.find(chosen_url)
            extra_text = source[:chosen_url_pos].strip() + "\n" + source[chosen_url_pos + len(chosen_url):].strip()
            extra_text = extra_text.strip()

            text = ""
            if title:
                text = f"{title}\n"
            text += f"\nОт пользователя {self.event.sender}"

            if self.event.platform == Platform.TG:
                text += f'\n{get_tg_formatted_url("Сурс", chosen_url)}'
            else:
                text += f"\n{chosen_url}"
            # Костыль, чтобы видосы которые шарятся с мобилы с реддита не дублировали title
            if extra_text and extra_text != title:
                text += f"\n{extra_text}"

            res = self.bot.parse_and_send_msgs({'text': text, 'attachments': attachments}, self.event.peer_id)
            if res[0]['success']:
                self.bot.delete_message(self.event.peer_id, self.event.message.id)

    def get_method_and_chosen_url(self, source):
        method = None
        urls = get_urls_from_text(source)
        for url in urls:
            hostname = urlparse(url).hostname
            if not hostname:
                raise PWarning("Не нашёл ссылки")
            for k in self.MEDIA_TRANSLATOR:
                if hostname in k:
                    return self.MEDIA_TRANSLATOR[k], url

        if not method:
            raise PWarning("Не youtube/tiktok/reddit/instagram ссылка")

    def get_youtube_video(self, url):
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
        if video_info['duration'] > 60:
            raise PWarning("Нельзя грузить видосы > 60 секунд с ютуба")
        video_urls = [x for x in video_info['formats'] if x['ext'] == 'mp4' and x.get('asr')]

        if len(video_urls) == 0:
            raise PWarning("Чёт проблемки, напишите разрабу и пришли ссылку на видео")
        max_quality_video = sorted(video_urls, key=lambda x: x['format_note'], reverse=True)[0]
        url = max_quality_video['url']
        video_content = requests.get(url).content
        attachments = [self.bot.upload_video(video_content, peer_id=self.event.peer_id)]
        return attachments, video_info['title']

    def get_tiktok_video(self, url):
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        content = requests.get(url, headers=headers).content
        bs4 = BeautifulSoup(content, 'html.parser')

        try:
            video_url = bs4.find('meta', attrs={'property': 'og:video'}).attrs['content']
        except:
            if "vt.tiktok" in url:
                data = json.loads(bs4.find("script", attrs={"id": "SIGI_STATE"}).text)
                video_url = data['ItemList']['video']['preloadList'][0]['url']
            else:
                data_str = bs4.find("script", attrs={"id": "sigi-persisted-data"}).text
                regexp = re.compile(r"window\['\w*'\]=")
                keys_positions = re.finditer(regexp, data_str)

                key = -1
                pos = -1
                data = {}
                for x in keys_positions:
                    if pos != -1:
                        data[key] = json.loads(data_str[pos: x.regs[0][0] - 1])
                    regexp = r"\['\w*'\]"
                    key = re.findall(regexp, data_str[x.regs[0][0]:x.regs[0][1]])[0] \
                        .replace("[", '') \
                        .replace("]", "") \
                        .strip("'") \
                        .strip('\\')
                    if key != -1:
                        pos = x.regs[0][1]
                data[key] = json.loads(data_str[pos: len(data_str)])
                if not data or "SIGI_STATE" not in data:
                    raise PWarning("Не смог распарсить Тикток видео")
                try:
                    video_url = data['SIGI_STATE']['ItemList']['video']['preloadList'][0]['url']
                except:
                    raise PWarning("Не смог распарсить Тикток видео")

        title = bs4.find('meta', attrs={'property': 'og:title'}).attrs['content']

        video = requests.get(video_url, headers=headers).content

        attachments = [self.bot.upload_video(video, peer_id=self.event.peer_id)]
        return attachments, title

    def get_reddit_attachment(self, url):
        rs = RedditSaver()
        attachment = rs.get_from_reddit(url)
        if rs.is_image or rs.is_images:
            attachments = self.bot.upload_photos(attachment, peer_id=self.event.peer_id)
        elif rs.is_video:
            attachments = self.bot.upload_video(attachment, peer_id=self.event.peer_id)
        elif rs.is_text or rs.is_link:
            text = attachment
            if self.event.platform == Platform.TG:
                text = text.replace("&#x200B;", "").replace("&amp;#x200B;", "").replace("&amp;", "&").replace(" ",
                                                                                                              " ").strip()
                p = re.compile(r"\[(.*)\]\((.*)\)")
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

            return [], f"{rs.title}\n\n{text}"
        else:
            raise PWarning("Я хз чё за контент")
        return attachments, rs.title

    def get_instagram_attachment(self, url):
        r = requests.get(url)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        if bs4.find("html", {'class': "not-logged-in"}):
            raise PWarning("Требуется логин для скачивания")
        if 'reel' in url:
            content_type = 'reel'
        else:
            try:
                content_type = bs4.find('meta', attrs={'name': 'medium'}).attrs['content']
            except Exception:
                raise PWarning("Ссылка на инстаграмм не является видео/фото")

        if content_type == 'image':
            photo_url = bs4.find('meta', attrs={'property': 'og:image'}).attrs['content']
            return self.bot.upload_photos([photo_url], peer_id=self.event.peer_id), ""
        elif content_type == 'video':
            try:
                video_url = bs4.find('meta', attrs={'property': 'og:video'}).attrs['content']
            except:
                raise PWarning("Не получилось распарсить видео с инстаграма")
            return [self.bot.upload_video(video_url, peer_id=self.event.peer_id)], ""
        elif content_type == 'reel':
            shared_data_text = "window._sharedData = "
            script_text = ";</script>"
            pos_start = r.text.find(shared_data_text) + len(shared_data_text)
            pos_end = r.text.find(script_text, pos_start)
            reel_data = json.loads(r.text[pos_start:pos_end])
            entry_data = reel_data['entry_data']
            if 'LoginAndSignupPage' in entry_data:
                raise PWarning("Этот reel скачать не получится, требуется авторизация :(")
            video_url = entry_data['PostPage'][0]['graphql']['shortcode_media']['video_url']
            return [self.bot.upload_video(video_url, peer_id=self.event.peer_id)], ""
        else:
            raise PWarning("Ссылка на инстаграмм не является видео/фото")

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
        headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(url, headers=headers)
        bs4 = BeautifulSoup(r.content, 'html.parser')
        player = bs4.select_one(".page-story .page-story__story .player")
        if not player:
            raise PWarning("Не нашёл видео в этом посте")
        title = bs4.find('meta', attrs={'property': 'og:title'}).attrs['content']
        webm = player.attrs['data-webm']
        video_content = requests.get(webm).content
        attachments = [self.bot.upload_video(video_content, peer_id=self.event.peer_id)]
        return attachments, title


class NothingLogger(object):
    @staticmethod
    def debug(msg):
        pass

    @staticmethod
    def warning(msg):
        pass

    @staticmethod
    def error(msg):
        pass
