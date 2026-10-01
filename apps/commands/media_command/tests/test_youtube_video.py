from types import SimpleNamespace
from unittest.mock import Mock, patch

import yt_dlp
from django.test import SimpleTestCase

from apps.bot.core.messages.message import Message
from apps.commands.media_command.service import MediaKeys, MediaServiceResponse
from apps.commands.media_command.services.youtube_video import YoutubeVideoService
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

    def test_get_video_download_urls_prefers_english_and_limited_video_when_original_is_not_marked(self):
        service = YoutubeVideo()

        video, audio, filesize_mb = service._get_video_download_urls(
            {
                "duration": 10,
                "media_type": "video",
                "formats": [
                    {
                        "format_id": "audio-en",
                        "resolution": "audio only",
                        "filesize": 10,
                        "language": "en-US",
                    },
                    {
                        "format_id": "audio-ru",
                        "resolution": "audio only",
                        "filesize": 20,
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
        self.assertEqual(audio["format_id"], "audio-en")
        self.assertGreater(filesize_mb, 0)

    def test_get_video_download_urls_prefers_original_audio_over_russian_dub(self):
        service = YoutubeVideo()

        _, audio, _ = service._get_video_download_urls(
            {
                "duration": 10,
                "media_type": "video",
                "formats": [
                    {
                        "format_id": "audio-ru-dub",
                        "resolution": "audio only",
                        "filesize": 20,
                        "language": "ru",
                        "language_preference": -1,
                    },
                    {
                        "format_id": "audio-en-original",
                        "resolution": "audio only",
                        "filesize": 10,
                        "language": "en-US",
                        "language_preference": 10,
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

        self.assertEqual(audio["format_id"], "audio-en-original")

    def test_get_video_download_urls_prefers_h264_and_aac_for_telegram(self):
        service = YoutubeVideo()
        info = self._get_video_info_with_formats(
            [
                {
                    "format_id": "251", "resolution": "audio only", "filesize": 303652,
                    "acodec": "opus", "language": "ar",
                },
                {
                    "format_id": "140", "resolution": "audio only", "filesize": 302904,
                    "acodec": "mp4a.40.2", "language": "ar", "url": "https://example.com/aac",
                },
                {
                    "format_id": "395", "vbr": 110, "ext": "mp4", "vcodec": "av01.0.00M.08",
                    "acodec": "none", "dynamic_range": "SDR", "width": 322, "height": 214,
                    "protocol": "https", "url": "https://example.com/av1",
                },
                {
                    "format_id": "133", "vbr": 90, "ext": "mp4", "vcodec": "avc1.4d400d",
                    "acodec": "none", "dynamic_range": "SDR", "width": 322, "height": 214,
                    "protocol": "https", "url": "https://example.com/h264",
                },
            ]
        )
        service._get_video_info = Mock(return_value=info)

        data = service.get_video_info("https://youtu.be/xhMYPSnO7ro")

        self.assertEqual(data.extra_data["video_format_id"], "133")
        self.assertEqual(data.extra_data["audio_format_id"], "140")
        self.assertEqual(data.extra_data["fallback_video_format_ids"], [])

    def test_original_audio_is_kept_even_if_only_dub_has_aac(self):
        service = YoutubeVideo()
        info = self._get_video_info_with_formats(
            [
                {
                    "format_id": "original", "resolution": "audio only", "filesize": 100,
                    "acodec": "opus", "language": "ar", "language_preference": 10,
                },
                {
                    "format_id": "dub", "resolution": "audio only", "filesize": 100,
                    "acodec": "mp4a.40.2", "language": "en", "language_preference": -1,
                },
                {
                    "format_id": "video", "vbr": 100, "ext": "mp4", "vcodec": "avc1",
                    "dynamic_range": "SDR", "width": 640, "height": 360,
                },
            ]
        )

        _, audio, _ = service._get_video_download_urls(info)

        self.assertEqual(audio["format_id"], "original")

    def test_original_aac_is_preferred_over_original_opus(self):
        service = YoutubeVideo()
        info = self._get_video_info_with_formats(
            [
                {
                    "format_id": "original-opus", "resolution": "audio only", "filesize": 110,
                    "acodec": "opus", "language": "ar", "language_preference": 10,
                },
                {
                    "format_id": "original-aac", "resolution": "audio only", "filesize": 100,
                    "acodec": "mp4a.40.2", "language": "ar", "language_preference": 10,
                },
                {
                    "format_id": "video", "vbr": 100, "ext": "mp4", "vcodec": "avc1",
                    "dynamic_range": "SDR", "width": 640, "height": 360,
                },
            ]
        )

        _, audio, _ = service._get_video_download_urls(info)

        self.assertEqual(audio["format_id"], "original-aac")

    def test_get_video_download_urls_uses_explicit_language(self):
        service = YoutubeVideo()
        video_info = self._get_video_info_with_formats(
            [
                {
                    "format_id": "audio-en-original",
                    "resolution": "audio only",
                    "filesize": 20,
                    "language": "en-US",
                    "language_preference": 10,
                },
                {
                    "format_id": "audio-ru",
                    "resolution": "audio only",
                    "filesize": 10,
                    "language": "ru",
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
            ]
        )

        _, audio, _ = service._get_video_download_urls(video_info, audio_language="ru")

        self.assertEqual(audio["format_id"], "audio-ru")

    def test_get_video_download_urls_matches_base_language_to_regional_track(self):
        service = YoutubeVideo()
        video_info = self._get_video_info_with_formats(
            [
                {
                    "format_id": "audio-en-us",
                    "resolution": "audio only",
                    "filesize": 10,
                    "language": "en-US",
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
            ]
        )

        _, audio, _ = service._get_video_download_urls(video_info, audio_language="en")

        self.assertEqual(audio["format_id"], "audio-en-us")

    def test_get_video_download_urls_reports_available_languages(self):
        service = YoutubeVideo()
        video_info = self._get_video_info_with_formats(
            [
                {
                    "format_id": "audio-en",
                    "resolution": "audio only",
                    "filesize": 10,
                    "language": "en-US",
                }
            ]
        )

        with self.assertRaisesMessage(PWarning, "Доступны: en-US"):
            service._get_video_download_urls(video_info, audio_language="ru")

    def test_normalize_audio_language_rejects_invalid_value(self):
        with self.assertRaisesMessage(PWarning, "Неверный язык аудиодорожки"):
            YoutubeVideo._normalize_audio_language("russian!")

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

    def test_shorts_prefer_direct_stream_over_hls_at_same_resolution(self):
        service = YoutubeVideo()
        info = self._get_video_info_with_formats(
            [
                {"format_id": "audio", "resolution": "audio only", "filesize": 10},
                {
                    "format_id": "hls-1080",
                    "vbr": 4000,
                    "ext": "mp4",
                    "vcodec": "avc1",
                    "dynamic_range": "SDR",
                    "width": 1080,
                    "height": 1920,
                    "protocol": "m3u8_native",
                },
                {
                    "format_id": "hls-720",
                    "vbr": 2400,
                    "ext": "mp4",
                    "vcodec": "avc1",
                    "dynamic_range": "SDR",
                    "width": 720,
                    "height": 1280,
                    "protocol": "m3u8_native",
                },
                {
                    "format_id": "https-720",
                    "vbr": 1900,
                    "ext": "mp4",
                    "vcodec": "avc1",
                    "dynamic_range": "SDR",
                    "width": 720,
                    "height": 1280,
                    "protocol": "https",
                },
                {
                    "format_id": "https-480",
                    "vbr": 1000,
                    "ext": "mp4",
                    "vcodec": "avc1",
                    "dynamic_range": "SDR",
                    "width": 480,
                    "height": 854,
                    "protocol": "https",
                },
            ]
        )
        info["media_type"] = "short"

        video, _, _ = service._get_video_download_urls(info)

        self.assertEqual(video["format_id"], "https-720")

    def test_hls_is_kept_when_no_direct_stream_has_matching_resolution(self):
        service = YoutubeVideo()
        info = self._get_video_info_with_formats(
            [
                {"format_id": "audio", "resolution": "audio only", "filesize": 10},
                {
                    "format_id": "hls-720",
                    "vbr": 2400,
                    "ext": "mp4",
                    "vcodec": "avc1",
                    "dynamic_range": "SDR",
                    "width": 720,
                    "height": 1280,
                    "protocol": "m3u8_native",
                },
                {
                    "format_id": "https-480",
                    "vbr": 1000,
                    "ext": "mp4",
                    "vcodec": "avc1",
                    "dynamic_range": "SDR",
                    "width": 480,
                    "height": 854,
                    "protocol": "https",
                },
            ]
        )
        info["media_type"] = "short"

        video, _, _ = service._get_video_download_urls(info)

        self.assertEqual(video["format_id"], "hls-720")

    def test_unavailable_video_format_falls_back_to_lower_direct_stream_with_same_audio(self):
        service = YoutubeVideo()
        info = self._get_video_info_with_formats(
            [
                {"format_id": "audio-en", "resolution": "audio only", "filesize": 10, "language": "en", "url": "https://example.com/audio"},
                {
                    "format_id": "https-720", "vbr": 2000, "ext": "mp4", "vcodec": "avc1", "dynamic_range": "SDR",
                    "width": 720, "height": 1280, "protocol": "https", "url": "https://example.com/video",
                },
                {
                    "format_id": "https-480", "vbr": 1000, "ext": "mp4", "vcodec": "avc1", "dynamic_range": "SDR",
                    "width": 480, "height": 854, "protocol": "https", "url": "https://example.com/video-low",
                },
                {
                    "format_id": "hls-720", "vbr": 2400, "ext": "mp4", "vcodec": "avc1", "dynamic_range": "SDR",
                    "width": 720, "height": 1280, "protocol": "m3u8_native", "url": "https://example.com/hls",
                },
            ]
        )
        info["media_type"] = "short"
        service._get_video_info = Mock(return_value=info)
        data = service.get_video_info("https://www.youtube.com/shorts/video-id", audio_language="en")
        self.assertEqual(data.extra_data["fallback_video_format_ids"], ["https-480", "hls-720"])

        unavailable = PWarning("Не смог найти видео")
        unavailable.__cause__ = yt_dlp.utils.DownloadError("HTTP Error 404: Not Found")
        service.downloader.download_to_bytes = Mock(side_effect=[unavailable, b"video-content"])

        attachment = service.download_video(data)

        self.assertEqual(attachment.content, b"video-content")
        self.assertEqual(
            [call.kwargs["ydl_params"]["format"] for call in service.downloader.download_to_bytes.call_args_list],
            [
                "https-720+audio-en/best[ext=mp4][vcodec!=none][acodec!=none]",
                "https-480+audio-en/best[ext=mp4][vcodec!=none][acodec!=none]",
            ],
        )

    def test_unrelated_download_error_does_not_try_other_format(self):
        service = YoutubeVideo()
        unavailable = PWarning("Не смог найти видео")
        unavailable.__cause__ = yt_dlp.utils.DownloadError("Video unavailable")
        service.downloader.download_to_bytes = Mock(side_effect=unavailable)
        with self.assertRaises(PWarning):
            service.download_video(
                VideoData(extra_data={
                    "source_url": "https://www.youtube.com/shorts/video-id",
                    "video_format_id": "video-720",
                    "fallback_video_format_ids": ["video-480"],
                })
            )

        service.downloader.download_to_bytes.assert_called_once()

    def test_fallback_stops_after_two_alternatives(self):
        service = YoutubeVideo()
        unavailable = PWarning("Не смог найти видео")
        unavailable.__cause__ = yt_dlp.utils.DownloadError("HTTP Error 404: Not Found")
        service.downloader.download_to_bytes = Mock(side_effect=unavailable)

        with self.assertRaises(PWarning):
            service.download_video(
                VideoData(extra_data={
                    "source_url": "https://www.youtube.com/shorts/video-id",
                    "video_format_id": "video-720",
                    "fallback_video_format_ids": ["video-480", "video-360", "video-240"],
                })
            )

        self.assertEqual(service.downloader.download_to_bytes.call_count, 3)

    def test_progressive_fallback_does_not_select_silent_video(self):
        info = self._get_video_info_with_formats([
            {
                "format_id": "progressive-720", "vbr": 1000, "ext": "mp4", "vcodec": "avc1",
                "acodec": "mp4a", "dynamic_range": "SDR", "width": 1280, "height": 720, "protocol": "https",
            },
            {
                "format_id": "silent-720", "vbr": 900, "ext": "mp4", "vcodec": "avc1",
                "acodec": "none", "dynamic_range": "SDR", "width": 1280, "height": 720, "protocol": "https",
            },
            {
                "format_id": "progressive-480", "vbr": 500, "ext": "mp4", "vcodec": "avc1",
                "acodec": "mp4a", "dynamic_range": "SDR", "width": 854, "height": 480, "protocol": "https",
            },
        ])

        self.assertEqual(
            YoutubeVideo._get_fallback_video_format_ids(info, info["formats"][0]),
            ["progressive-480"],
        )

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


class YoutubeVideoLanguageOptionTests(SimpleTestCase):
    def test_media_keys_extracts_audio_language(self):
        message = Message("/медиа --lang-en https://youtube.com/watch?v=video-id")
        media_keys = MediaKeys(message.keys, message.short_keys)

        self.assertTrue(media_keys.language_en)
        self.assertFalse(media_keys.language_ru)

    def test_language_specific_download_uses_separate_cache_identity(self):
        event = SimpleNamespace(log_filter={})
        service = YoutubeVideoService(
            Mock(),
            event,
            media_keys=MediaKeys([], []),
            has_command_name=True,
        )
        cached_response = MediaServiceResponse(text="cached")
        service._get_cached = Mock(return_value=cached_response)

        result = service._get_content_by_url(
            VideoData(
                channel_id="channel-id",
                video_id="video-id",
                title="Video",
                extra_data={"audio_language": "ru"},
            ),
            "https://www.youtube.com/watch?v=video-id",
        )

        self.assertIs(result, cached_response)
        service._get_cached.assert_called_once_with("channel-id", "video-id:ru", "Video")


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

    def test_download_to_bytes_retries_truncated_response_with_fresh_download(self):
        downloader = YtDlpVideoDownloader()
        with patch("apps.shared.utils.video.yt_dlp_video_downloader.time.sleep") as sleep:
            with patch.object(
                downloader,
                "_download_to_bytes",
                side_effect=[
                    yt_dlp.utils.DownloadError("1130496 bytes read, 688189 more expected"),
                    b"video-content",
                ],
            ) as download:
                content = downloader.download_to_bytes("https://example.com/video")

        self.assertEqual(content, b"video-content")
        self.assertEqual(download.call_count, 2)
        sleep.assert_called_once_with(downloader.DEFAULT_DOWNLOAD_RETRY_DELAY)

    def test_download_to_bytes_does_not_retry_non_transient_error(self):
        downloader = YtDlpVideoDownloader()
        with patch.object(
            downloader,
            "_download_to_bytes",
            side_effect=yt_dlp.utils.DownloadError("Video unavailable"),
        ) as download:
            with self.assertRaises(PWarning):
                downloader.download_to_bytes("https://example.com/video")

        download.assert_called_once()
