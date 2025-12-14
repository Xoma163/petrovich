import subprocess
import tempfile
from pathlib import Path
from time import sleep

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.bot.api.media.youtube.video import YoutubeVideo
from apps.bot.classes.bots.tg_bot import TgBot
from apps.bot.classes.const.consts import ATTACHMENT_TYPE_TRANSLATOR
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.utils.utils import get_youtube_video_id
from apps.service.models import Meme

tg_bot = TgBot()


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.get_meme_files()
        self.get_meme_file_previews()

    def get_meme_files(self):
        print("get_meme_files")
        memes = Meme.objects.filter(file="").order_by('id')
        for i, meme in enumerate(memes):
            print(f"Processing {i + 1} of {len(memes) + 1}. id={meme.id}")
            try:
                if not meme.tg_file_id:
                    raise RuntimeError("can't get tg_file_id")
                att = ATTACHMENT_TYPE_TRANSLATOR[meme.type]()
                att.file_id = meme.tg_file_id
                att.get_file()
                if not att.private_download_url:
                    raise RuntimeError("can't get private_download_url")
                else:
                    content = att.download_content(use_proxy=True)

                detected_ext = self.detect_ext(content)
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
            print(f"Processing {i + 1} of {len(memes) + 1}. id={meme.id}")
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
        if not video_id:
            print("no meme.video_id")
            print(meme.link)
            return None

        if not video_id:
            print("not video_id")
            print(meme.link)
            return None

        preview_url = f"https://img.youtube.com/vi/{video_id}/default.jpg"
        att = PhotoAttachment()
        att.public_download_url = preview_url
        content = att.download_content(use_proxy=True)
        if len(content) == 1097:  # default youtube preview
            content = self.get_preview_by_video_content(meme)
        return content

    def _get_meme_file_previews_content(self, meme):
        return self.get_preview_by_video_content(meme)

    def get_preview_by_video_content(self, meme):
        return self.video_bytes_to_jpeg_at_1s(meme.file.read())

    @staticmethod
    def video_bytes_to_jpeg_at_1s(video_bytes: bytes) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name
        out_path = tmp_path + ".jpg"
        try:
            cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", "1.0",
                "-i", tmp_path,
                "-frames:v", "1",
                "-vf", "scale=120:90:flags=lanczos",
                "-q:v", "2",
                out_path
            ]
            subprocess.check_call(cmd)
            return Path(out_path).read_bytes()
        finally:
            try:
                Path(tmp_path).unlink()
            except:
                pass
            try:
                Path(out_path).unlink()
            except:
                pass

    @staticmethod
    def get_youtube_content(meme):
        yt_service = YoutubeVideo(use_proxy=True)
        video_data = yt_service.get_video_info(meme.link)
        va = yt_service.download_video(video_data)
        return va.content

    @staticmethod
    def detect_ext(b: bytes) -> str | None:
        if not b:
            return None

        if b.startswith(b'\xFF\xD8\xFF'):
            return "jpg"

        if b.startswith(b'GIF87a') or b.startswith(b'GIF89a'):
            return "gif"

        if len(b) >= 12 and b[4:8] == b'ftyp':
            return "mp4"
        idx = b.find(b'ftyp', 0, 64)
        if idx != -1 and idx + 4 + 4 <= len(b):
            return "mp4"

        if b.startswith(b'OggS'):
            return "ogg"

        if len(b) >= 12 and b[0:4] == b'RIFF' and b[8:12] == b'WEBP':
            return "webp"

        return None
