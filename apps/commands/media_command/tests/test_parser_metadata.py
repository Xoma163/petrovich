import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from apps.commands.media_command.services.coub import CoubService
from apps.connectors.parsers.media_command.boosty import Boosty
from apps.connectors.parsers.media_command.pinterest import Pinterest, PinterestDataItem
from apps.connectors.parsers.media_command.reddit import Reddit
from apps.connectors.parsers.media_command.sunoai import SunoAI
from apps.shared.exceptions import PWarning


class ParserMetadataTests(SimpleTestCase):
    def test_reddit_audio_manifest_layouts_and_missing_elements(self):
        manifests = [
            ('<AdaptationSet contentType="audio"><Representation><BaseURL>audio.m4a</BaseURL>'
             '</Representation></AdaptationSet>', "audio.m4a"),
            ('<Representation id="AUDIO-1"><BaseURL>fallback.m4a</BaseURL></Representation>', "fallback.m4a"),
            ('<AdaptationSet contentType="audio"><Representation/></AdaptationSet>'
             '<Representation id="AUDIO-1"><BaseURL>fallback.m4a</BaseURL></Representation>', "fallback.m4a"),
            ('<AdaptationSet contentType="audio"/>', None),
            ('<Representation id="AUDIO-1"/>', None),
            ("<MPD/>", None),
        ]
        for manifest, expected in manifests:
            with self.subTest(manifest=manifest), patch(
                "apps.connectors.parsers.media_command.reddit.requests.get",
                return_value=Mock(content=manifest.encode()),
            ):
                self.assertEqual(Reddit._parse_mpd_audio_filename("https://example.com/manifest.mpd"), expected)

    def test_boosty_missing_or_invalid_state_produces_warning(self):
        pages = [
            "<html>Login required</html>",
            '<script id="initial-state">invalid JSON</script>',
            '<script id="initial-state">null</script>',
            '<script id="initial-state">{"posts":{"postsList":{"data":{"posts":[]}}}}</script>',
        ]
        for html in pages:
            with self.subTest(html=html), patch(
                "apps.connectors.parsers.media_command.boosty.requests.get",
                return_value=Mock(text=html),
            ), self.assertRaises(PWarning):
                Boosty.get_video_info("https://boosty.to/example/posts/test")

    def test_coub_missing_or_invalid_metadata_does_not_create_attachment(self):
        bot = Mock()
        service = CoubService(bot, SimpleNamespace(peer_id=1, message_thread_id=None), None, False)
        for html in (
            "<html>Not found</html>",
            '<script id="coubPageCoubJson">not JSON</script>',
            '<script id="coubPageCoubJson">{}</script>',
            '<script id="coubPageCoubJson">{"title":"test","file_versions":{"share":{"default":null}}}</script>',
        ):
            with self.subTest(html=html), patch(
                "apps.commands.media_command.services.coub.requests.get",
                return_value=Mock(content=html.encode()),
            ), self.assertRaises(PWarning):
                service.get_content_by_url("https://coub.com/view/example")
        bot.get_video_attachment.assert_not_called()

    def test_coub_valid_metadata_keeps_caption_and_video(self):
        bot = Mock()
        service = CoubService(bot, SimpleNamespace(peer_id=1, message_thread_id=2), None, False)
        data = {"title": "Caption", "file_versions": {"share": {"default": "https://example.com/video.mp4"}}}
        html = f'<script id="coubPageCoubJson">{json.dumps(data)}</script>'
        with patch(
            "apps.commands.media_command.services.coub.requests.get",
            return_value=Mock(content=html.encode()),
        ):
            result = service.get_content_by_url("https://coub.com/view/example")
        self.assertEqual(result.text, "Caption")
        self.assertEqual(result.attachments, [bot.get_video_attachment.return_value])
        bot.get_video_attachment.assert_called_once_with(
            url="https://example.com/video.mp4", peer_id=1, message_thread_id=2,
        )

    def test_pinterest_photo_uses_meta_fallback(self):
        for snippet in ("", '<script data-test-id="leaf-snippet">invalid JSON</script>'):
            with self.subTest(snippet=snippet):
                html = snippet + '<meta name="og:image" content="https://example.com/animation.gif">'
                item = Pinterest._get_photo(BeautifulSoup(html, "html.parser"))
                self.assertEqual(item.download_url, "https://example.com/animation.gif")
                self.assertEqual(item.content_type, PinterestDataItem.CONTENT_TYPE_GIF)
                self.assertEqual(item.caption, "")

    def test_pinterest_photo_keeps_structured_metadata(self):
        data = {"headline": "Caption", "image": "https://example.com/photo.jpg"}
        html = f'<script data-test-id="leaf-snippet">{json.dumps(data)}</script>'
        item = Pinterest._get_photo(BeautifulSoup(html, "html.parser"))
        self.assertEqual(item.caption, "Caption")
        self.assertEqual(item.download_url, data["image"])
        self.assertEqual(item.content_type, PinterestDataItem.CONTENT_TYPE_IMAGE)

    def test_pinterest_missing_image_url_produces_warning(self):
        for html in ("<html/>", '<meta name="og:image">'):
            with self.subTest(html=html), self.assertRaises(PWarning):
                Pinterest._get_photo(BeautifulSoup(html, "html.parser"))

    def test_pinterest_video_without_title_is_valid(self):
        html = '<script data-test-id="video-snippet">{"contentUrl":"https://example.com/video.mp4"}</script>'
        item = Pinterest._get_video(BeautifulSoup(html, "html.parser"))
        self.assertEqual(item.download_url, "https://example.com/video.mp4")
        self.assertEqual(item.caption, "")

    def test_pinterest_missing_or_invalid_video_produces_warning(self):
        for html in (
            "<html/>",
            '<script data-test-id="video-snippet">invalid JSON</script>',
            '<script data-test-id="video-snippet">{}</script>',
            '<script data-test-id="video-snippet">{"contentUrl":null}</script>',
        ):
            with self.subTest(html=html), self.assertRaises(PWarning):
                Pinterest._get_video(BeautifulSoup(html, "html.parser"))

    def test_suno_missing_audio_produces_warning(self):
        for html in ("<html>Login required</html>", '<meta property="og:audio">'):
            with self.subTest(html=html), patch(
                "apps.connectors.parsers.media_command.sunoai.requests.post",
                return_value=Mock(content=html.encode(), text=html),
            ), self.assertRaises(PWarning):
                SunoAI.get_info("https://suno.com/song/example")

    def test_suno_optional_metadata_can_be_absent(self):
        html = '<meta property="og:audio" content="https://example.com/song.mp3">'
        with patch(
            "apps.connectors.parsers.media_command.sunoai.requests.post",
            return_value=Mock(content=html.encode(), text=html),
        ):
            item = SunoAI.get_info("https://suno.com/song/example")
        self.assertEqual(item.download_url, "https://example.com/song.mp3")
        self.assertEqual(item.title, "Аудио из Suno")
        self.assertIsNone(item.thumbnail_url)

    def test_suno_valid_metadata_keeps_title_image_and_author(self):
        html = (
            '<meta property="og:title" content="Song | Suno">'
            '<meta property="og:audio" content="https://example.com/song.mp3">'
            '<meta property="og:image" content="https://example.com/image.jpg">'
            r'"display_name\":\"Artist\"'
        )
        with patch(
            "apps.connectors.parsers.media_command.sunoai.requests.post",
            return_value=Mock(content=html.encode(), text=html),
        ):
            item = SunoAI.get_info("https://suno.com/song/example")
        self.assertEqual(item.title, "Song")
        self.assertEqual(item.thumbnail_url, "https://example.com/image.jpg")
        self.assertEqual(item.artists, "Artist")
