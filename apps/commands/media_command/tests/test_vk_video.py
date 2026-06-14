from django.test import SimpleTestCase

from apps.connectors.parsers.media_command.vk_video import VKVideo
from apps.shared.exceptions import PWarning


class VKVideoTests(SimpleTestCase):
    def test_clear_url_removes_playlist_noise(self):
        url = "https://vkvideo.ru/video-1_2?list=abc&section=all&utm=test#fragment"

        self.assertEqual(
            VKVideo.clear_url(url),
            "https://vkvideo.ru/video-1_2?utm=test",
        )

    def test_check_url_is_video_allows_video_and_clip_links(self):
        VKVideo.check_url_is_video("https://vk.com/video-1_2")
        VKVideo.check_url_is_video("https://vkvideo.ru/clip-1_2")
        VKVideo.check_url_is_video("https://vk.com/video?z=video-1_2%2Fpl_cat_updates")

    def test_check_url_is_video_rejects_channel_links(self):
        with self.assertRaises(PWarning):
            VKVideo.check_url_is_video("https://vkvideo.ru/@channel")
