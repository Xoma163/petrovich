from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.connectors.parsers.media_command.data import VideoData
from apps.connectors.parsers.media_command.youtube.video import YoutubeVideo


class YoutubeVideoTests(SimpleTestCase):
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

    def test_download_video_uses_selected_format_ids(self):
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
                "js_runtimes": {"deno": {}},
                "remote_components": ["ejs:npm", "ejs:github"],
                "format": "video-720+audio-ru",
                "merge_output_format": "mp4",
            },
        )
