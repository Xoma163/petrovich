from unittest.mock import Mock, patch

import yt_dlp
from django.test import SimpleTestCase

from apps.connectors.parsers.media_command.data import VideoData
from apps.connectors.parsers.media_command.youtube.video import YoutubeVideo
from apps.shared.exceptions import PWarning
from apps.shared.utils.video.yt_dlp_video_downloader import YtDlpVideoDownloader


class YoutubeVideoTests(SimpleTestCase):
    @staticmethod
    def _get_video_info_with_formats(formats):
        return {
            "id": "video-id",
            "title": "Video",
            "duration": 10,
            "width": 640,
            "height": 360,
            "channel_id": "channel-id",
            "channel": "Channel",
            "media_type": "video",
            "thumbnails": [],
            "formats": formats,
        }

    def test_get_video_download_urls_prefers_ru_audio_and_limited_video(self):
        service = YoutubeVideo()

        video, audio, filesize_mb = service._get_video_download_urls(
            {
                "duration": 10,
                "media_type": "video",
                "formats": [
                    {
                        "format_id": "audio-en",
                        "resolution": "audio only",
                        "filesize": 20,
                        "language": "en-US",
                    },
                    {
                        "format_id": "audio-ru",
                        "resolution": "audio only",
                        "filesize": 10,
                        "language": "ru",
                    },
                    {
                        "format_id": "video-1080",
                        "vbr": 200,
                        "ext": "mp4",
                        "vcodec": "avc1",
                        "dynamic_range": "SDR",
                        "height": 1080,
                        "width": 1920,
                    },
                    {
                        "format_id": "video-720",
                        "vbr": 100,
                        "ext": "mp4",
                        "vcodec": "avc1",
                        "dynamic_range": "SDR",
                        "height": 720,
                        "width": 1280,
                    },
                ],
            },
        )

        self.assertEqual(video["format_id"], "video-720")
        self.assertEqual(audio["format_id"], "audio-ru")
        self.assertGreater(filesize_mb, 0)

    def test_get_video_download_urls_uses_high_resolution_when_requested(self):
        service = YoutubeVideo()

        video, _, _ = service._get_video_download_urls(
            {
                "duration": 10,
                "media_type": "video",
                "formats": [
                    {
                        "format_id": "audio",
                        "resolution": "audio only",
                        "filesize": 10,
                    },
                    {
                        "format_id": "video-1080",
                        "vbr": 200,
                        "ext": "mp4",
                        "vcodec": "avc1",
                        "dynamic_range": "SDR",
                        "height": 1080,
                        "width": 1920,
                    },
                    {
                        "format_id": "video-720",
                        "vbr": 100,
                        "ext": "mp4",
                        "vcodec": "avc1",
                        "dynamic_range": "SDR",
                        "height": 720,
                        "width": 1280,
                    },
                ],
            },
            high_res=True,
        )

        self.assertEqual(video["format_id"], "video-1080")

    @patch(
        "apps.connectors.parsers.media_command.youtube.video.shutil.which",
        return_value="/opt/projects/petrovich/.venv/bin/deno",
    )
    def test_download_video_uses_selected_format_ids(self, _):
        service = YoutubeVideo()
        service.downloader.download_to_bytes = Mock(return_value=b"video-content")

        attachment = service.download_video(
            VideoData(
                duration=10,
                width=1280,
                height=720,
                thumbnail_url="https://example.com/thumbnail.jpg",
                extra_data={
                    "source_url": "https://www.youtube.com/watch?v=video-id",
                    "video_format_id": "video-720",
                    "audio_format_id": "audio-ru",
                },
            ),
        )

        self.assertEqual(attachment.content, b"video-content")
        self.assertEqual(attachment.width, 1280)
        self.assertEqual(attachment.height, 720)
        service.downloader.download_to_bytes.assert_called_once_with(
            "https://www.youtube.com/watch?v=video-id",
            ydl_params={
                "noplaylist": True,
                "js_runtimes": {"deno": {"path": "/opt/projects/petrovich/.venv/bin/deno"}},
                "remote_components": ["ejs:npm", "ejs:github"],
                "format": "video-720+audio-ru/best[ext=mp4][vcodec!=none][acodec!=none]",
                "merge_output_format": "mp4",
            },
        )

    @patch("apps.connectors.parsers.media_command.youtube.video.Path.is_file", return_value=True)
    @patch("apps.connectors.parsers.media_command.youtube.video.sys.executable", "C:\\app\\.venv\\Scripts\\python.exe")
    @patch("apps.connectors.parsers.media_command.youtube.video.shutil.which", return_value=None)
    def test_ydl_params_find_deno_next_to_virtualenv_python(self, _, __):
        params = YoutubeVideo._get_ydl_params()

        self.assertEqual(params["js_runtimes"], {"deno": {"path": "C:\\app\\.venv\\Scripts\\deno.exe"}})

    def test_get_video_info_retries_incomplete_format_response(self):
        service = YoutubeVideo()
        incomplete_info = self._get_video_info_with_formats(
            [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                    "dynamic_range": "SDR",
                    "width": 640,
                    "height": 360,
                    "url": "https://example.com/progressive.mp4",
                    "filesize": 100,
                }
            ]
        )
        complete_info = self._get_video_info_with_formats(
            [
                {
                    "format_id": "audio",
                    "resolution": "audio only",
                    "filesize": 10,
                    "url": "https://example.com/audio.m4a",
                },
                {
                    "format_id": "video",
                    "vbr": 100,
                    "ext": "mp4",
                    "vcodec": "avc1",
                    "dynamic_range": "SDR",
                    "height": 720,
                    "width": 1280,
                    "url": "https://example.com/video.mp4",
                },
            ]
        )
        service._get_video_info = Mock(side_effect=[incomplete_info, complete_info])

        data = service.get_video_info("https://www.youtube.com/watch?v=video-id")

        self.assertEqual(service._get_video_info.call_count, 2)
        self.assertEqual(data.extra_data["video_format_id"], "video")
        self.assertEqual(data.extra_data["audio_format_id"], "audio")

    def test_get_video_info_falls_back_to_progressive_format(self):
        service = YoutubeVideo()
        incomplete_info = self._get_video_info_with_formats(
            [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                    "dynamic_range": "SDR",
                    "width": 640,
                    "height": 360,
                    "url": "https://example.com/progressive.mp4",
                    "filesize": 100,
                }
            ]
        )
        service._get_video_info = Mock(return_value=incomplete_info)

        data = service.get_video_info("https://www.youtube.com/watch?v=video-id")

        self.assertEqual(service._get_video_info.call_count, service.VIDEO_INFO_EXTRACTION_ATTEMPTS)
        self.assertEqual(data.extra_data["video_format_id"], "18")
        self.assertIsNone(data.extra_data["audio_format_id"])
        self.assertIsNone(data.audio_download_url)

    @patch(
        "apps.connectors.parsers.media_command.youtube.video.shutil.which",
        return_value="/opt/projects/petrovich/.venv/bin/deno",
    )
    def test_download_video_uses_progressive_format_without_audio_merge(self, _):
        service = YoutubeVideo()
        service.downloader.download_to_bytes = Mock(return_value=b"video-content")

        service.download_video(
            VideoData(
                extra_data={
                    "source_url": "https://www.youtube.com/watch?v=video-id",
                    "video_format_id": "18",
                    "audio_format_id": None,
                }
            )
        )

        service.downloader.download_to_bytes.assert_called_once_with(
            "https://www.youtube.com/watch?v=video-id",
            ydl_params={
                "noplaylist": True,
                "js_runtimes": {"deno": {"path": "/opt/projects/petrovich/.venv/bin/deno"}},
                "remote_components": ["ejs:npm", "ejs:github"],
                "format": "18",
                "merge_output_format": "mp4",
            },
        )


class YtDlpVideoDownloaderTests(SimpleTestCase):
    def test_download_to_bytes_retries_timeout_with_fresh_download(self):
        downloader = YtDlpVideoDownloader()
        with patch("apps.shared.utils.video.yt_dlp_video_downloader.time.sleep") as sleep:
            with patch.object(
                downloader,
                "_download_to_bytes",
                side_effect=[
                    yt_dlp.utils.DownloadError("Read timed out"),
                    b"video-content",
                ],
            ) as download:
                content = downloader.download_to_bytes("https://example.com/video")

        self.assertEqual(content, b"video-content")
        self.assertEqual(download.call_count, 2)
        sleep.assert_called_once_with(downloader.DEFAULT_DOWNLOAD_RETRY_DELAY)

    def test_download_to_bytes_does_not_retry_non_timeout_error(self):
        downloader = YtDlpVideoDownloader()
        with patch.object(
            downloader,
            "_download_to_bytes",
            side_effect=yt_dlp.utils.DownloadError("Video unavailable"),
        ) as download:
            with self.assertRaises(PWarning):
                downloader.download_to_bytes("https://example.com/video")

        download.assert_called_once()
