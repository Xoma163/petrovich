from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from urllib3.exceptions import ReadTimeoutError

from apps.connectors.parsers.media_command.instagram import InstagramParser
from apps.shared.exceptions import PWarning


class InstagramParserTests(SimpleTestCase):
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
        with self.assertRaisesMessage(PWarning, "Убедитесь в браузере"):
            InstagramParser().get_data("https://www.instagram.com/reel/DdUMTjbNbzH/")
