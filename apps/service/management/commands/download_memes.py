from time import sleep

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.bot.api.media.youtube.video import YoutubeVideo
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.const.consts import ATTACHMENT_TYPE_TRANSLATOR
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.attachments.video import VideoAttachment
from apps.bot.utils.utils import get_youtube_video_id, detect_ext
from apps.bot.utils.video.video_handler import VideoHandler
from apps.service.models import Meme

tg_bot = TgBot()


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.get_meme_files()
        self.get_meme_file_previews()

    @staticmethod
    def get_meme_files():
        print("get_meme_files")
        memes = Meme.objects.filter(file="").order_by('id')
        for i, meme in enumerate(memes):
            print(f"Processing {i + 1} of {len(memes)}. id={meme.id}")
            try:
                if not meme.tg_file_id:
                    raise RuntimeError("can't get tg_file_id")
                att = ATTACHMENT_TYPE_TRANSLATOR[meme.type]()
                att.file_id = meme.tg_file_id
                att.get_file()
                if not att.private_download_url and not att.private_download_path:
                    raise RuntimeError("can't get private_download_url/private_download_path")
                else:
                    content = att.download_content()

                detected_ext = detect_ext(content)
                if not detected_ext:
                    raise RuntimeError("can't detect ext")
                filename = f"{meme.id}.{detected_ext}"
                meme.file.save(filename, ContentFile(content))
                att.content = None
            except Exception as e:
                print(e)
            sleep(1)

    def get_meme_file_previews(self):
        print("get_meme_file_previews")
        no_file_preview_q = Q(file_preview__isnull=True) | Q(file_preview="")
        memes = Meme.objects.filter(type='video').filter(no_file_preview_q).order_by('id')
        for i, meme in enumerate(memes):
            print(f"Processing {i + 1} of {len(memes)}. id={meme.id}")
            try:
                if meme.link:
                    content = self._get_meme_file_previews_link(meme)
                else:
                    content = self._get_meme_file_previews_content(meme)
                if not content:
                    continue
                filename = f"{meme.id}_preview.jpg"
                meme.file_preview.save(filename, ContentFile(content))
            except Exception as e:
                print(e)
            sleep(1)

    def _get_meme_file_previews_link(self, meme):
        video_id = get_youtube_video_id(meme.link)
        preview_url = f"https://img.youtube.com/vi/{video_id}/default.jpg"
        att = PhotoAttachment()
        att.public_download_url = preview_url
        content = att.download_content()
        if len(content) == 1097:  # default youtube preview
            content = self._get_meme_file_previews_content(meme)
        return content

    @staticmethod
    def _get_meme_file_previews_content(meme):
        att = VideoAttachment()
        att.content = meme.file.read()
        vh = VideoHandler(video=att)
        return vh.get_preview()

    @staticmethod
    def get_youtube_content(meme) -> bytes:
        yt_service = YoutubeVideo()
        video_data = yt_service.get_video_info(meme.link)
        va = yt_service.download_video(video_data)
        return va.content
