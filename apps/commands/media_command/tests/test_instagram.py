import json
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from urllib3.exceptions import ReadTimeoutError

from apps.connectors.parsers.media_command.instagram import InstagramParser
from apps.shared.exceptions import PWarning


class InstagramParserTests(SimpleTestCase):
    @staticmethod
    def reels_feed_page(codes):
        feed = {
            "edges": [
                {
                    "node": {
                        "code": code,
                        "video_versions": [{"url": f"https://example.com/{code}.mp4"}],
                        "caption": {"text": "Reel caption"},
                    },
                }
                for code in codes
            ],
        }
        result = {"__bbox": {"result": {"data": {"xig_logged_out_reels_feed": feed}}}}
        cache = {"require": [["RelayPrefetchedStreamCache", "next", [], ["query", result]]]}
        payload = {"require": [["ScheduledServerJS", "handle", None, [{"__bbox": cache}]]]}
        return (
            '<script type="application/json" data-content-len="1000" data-processed="true">'
            + json.dumps(payload)
            + '</script>'
        )

    @patch.object(InstagramParser, "_get_instagram_request")
    def test_logged_out_feed_selects_requested_reel_not_recommendation(self, request):
        request.return_value = self.reels_feed_page(["recommended", "Dfe4_bAAFJN", "another"])

        for path in ("reel", "reels"):
            with self.subTest(path=path):
                data = InstagramParser().get_data(f"https://www.instagram.com/{path}/Dfe4_bAAFJN/")

                self.assertEqual(len(data.items), 1)
                self.assertEqual(data.items[0].download_url, "https://example.com/Dfe4_bAAFJN.mp4")
                self.assertEqual(data.caption, "")

    @patch.object(InstagramParser, "_get_instagram_request")
    def test_logged_out_feed_missing_requested_reel_does_not_return_recommendation(self, request):
        request.return_value = self.reels_feed_page(["recommended"])

        with self.assertRaises(PWarning):
            InstagramParser().get_data("https://www.instagram.com/reels/Dfe4_bAAFJN/")

    def test_logged_out_feed_json_fallback(self):
        page = self.reels_feed_page(["recommended", "Dfe4_bAAFJN"])

        media = InstagramParser().get_media_by_parse_json(page, shortcode="Dfe4_bAAFJN")

        self.assertEqual(media["code"], "Dfe4_bAAFJN")

    @patch("apps.connectors.parsers.media_command.instagram.WebDriverWait")
    @patch("apps.connectors.parsers.media_command.instagram.get_web_driver")
    def test_webdriver_wait_accepts_logged_out_reels_feed(self, get_web_driver, web_driver_wait):
        driver = Mock(page_source=self.reels_feed_page(["Dfe4_bAAFJN"]))
        get_web_driver.return_value = driver
        web_driver_wait.return_value.until.side_effect = lambda predicate: self.assertTrue(predicate(driver))

        self.assertEqual(
            InstagramParser()._get_instagram_request("https://www.instagram.com/reels/Dfe4_bAAFJN/"),
            driver.page_source,
        )
        driver.quit.assert_called_once_with()

    @patch("apps.shared.decorators.time.sleep")
    @patch("apps.connectors.parsers.media_command.instagram.WebDriverWait")
    @patch("apps.connectors.parsers.media_command.instagram.get_web_driver")
    def test_instagram_request_retries_webdriver_read_timeout(self, get_web_driver, web_driver_wait, sleep):
        timed_out_driver = Mock()
        timed_out_driver.get.side_effect = ReadTimeoutError(None, "/session", "timed out")
        successful_driver = Mock(page_source="instagram page")
        get_web_driver.side_effect = [timed_out_driver, successful_driver]

        result = InstagramParser()._get_instagram_request("https://www.instagram.com/reel/DdUMTjbNbzH/")

        self.assertEqual(result, "instagram page")
        self.assertEqual(get_web_driver.call_count, 2)
        timed_out_driver.quit.assert_called_once_with()
        successful_driver.quit.assert_called_once_with()
        web_driver_wait.assert_called_once_with(successful_driver, 5)
        sleep.assert_not_called()

    @patch.object(
        InstagramParser,
        "_get_instagram_request",
        side_effect=ReadTimeoutError(None, "/session", "timed out"),
    )
    def test_get_data_converts_webdriver_read_timeout_to_warning(self, _get_instagram_request):
        with self.assertRaisesMessage(PWarning, "Не удалось дождаться данных Instagram"):
            InstagramParser().get_data("https://www.instagram.com/reel/DdUMTjbNbzH/")
