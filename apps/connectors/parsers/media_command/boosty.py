import json

import requests
from bs4 import BeautifulSoup

from apps.bot.core.messages.attachments.video import VideoAttachment
from apps.connectors.parsers.media_command.data import VideoData
from apps.shared.exceptions import PWarning, PError


class Boosty:
    DOWNLOAD_CHUNK_SIZE = 10 * 1024 * 1024  # 10mb

    @staticmethod
    def get_video_info(post_url, auth_cookie=None) -> VideoData:
        cookies = {}
        if auth_cookie:
            cookies['auth'] = auth_cookie
        response = requests.get(post_url, cookies=cookies)
        bs4 = BeautifulSoup(response.text, 'html.parser')
        data = json.loads(bs4.select_one('#initial-state').text)
        post = data['posts']['postsList']['data']['posts'][0]
        post_data = post['data']
        if not post_data:
            raise PWarning(
                "Скорее всего пост платный и бот не знает ваших доступов для скачивания. Если вы подписаны и сами можете воспроизвести видео, тогда следуйте этой инструкции:\n"
                "1. Откройте пост в любом браузере\n"
                "2. Нажмите F12 и перейдите во вкладку Application(Приложение)\n"
                "3. Слева во вкладке Storage(Хранилище) найдите вкладку Cookies, выберите там сайт boosty.to\n"
                "4. Скопируйте содержимое auth\n"
                "5. Пришлите мне снова ссылку на видео и на следующей строчке содержимое auth\n"
                "6. Ваши данные нигде не сохраняются и единственное место где они будут лежать - этот чат. Поэтому не забывайте удалять сообщение с вашими куками. Куки меняются раз в 7 дней\n"
                "\n"
                "Пример (вместо точек будет набор символов):\n"
                "https://boosty.to/amazinguser/posts/12345678-aabb-ccdd-eeff-123456789012\n"
                "...accessToken...refreshToken...expiresAt......"
            )
        video_info = [x for x in post_data if x.get('vid')][0]

        author_id = post['user']['id']
        author_name = post['user']['name']
        post_title = post['title']
        video_id = video_info['vid']
        width = video_info['width']
        height = video_info['height']
        thumbnail = video_info.get('defaultPreview', 'preview')

        try:
            description = "\n".join([json.loads(x['content'])[0] for x in post_data if x.get('content')])
        except:
            description = None

        player_urls_dict = {x['type']: x['url'] for x in video_info['playerUrls'] if x['url']}

        return VideoData(
            title=post_title,
            description=description,
            channel_id=author_id,
            channel_title=author_name,
            video_id=video_id,
            width=width,
            height=height,
            thumbnail_url=thumbnail,
            extra_data={'player_urls_dict': player_urls_dict}
        )

    @staticmethod
    def _set_download_url(video_data: VideoData, high_res=False):
        player_urls_dict = video_data.extra_data['player_urls_dict']
        qualities_order = ['ultra_hd', 'quad_hd', 'full_hd', 'high', 'medium', 'low']
        if not high_res:
            qualities_order = qualities_order[2:]

        for quality in qualities_order:
            video_url = player_urls_dict.get(quality)
            if video_url:
                video_data.video_download_url = video_url
                break
        else:
            raise PError("Не смог найти видео")

    def download(self, video_data: VideoData, high_res=False) -> VideoAttachment:
        self._set_download_url(video_data, high_res)
        va = VideoAttachment()
        va.public_download_url = video_data.video_download_url
        va.download_content(headers={}, chunk_size=self.DOWNLOAD_CHUNK_SIZE)
        return va
