import json
from unittest.mock import Mock

from django.test import SimpleTestCase

from apps.bot.core.connectors.telegram.telegram import TelegramAPI, TelegramAPIRequestMode


class TelegramAPIInlineQueryTestCase(SimpleTestCase):
    def test_answer_inline_query_sends_pagination_and_personal_cache_fields(self):
        api = TelegramAPI("token", TelegramAPIRequestMode.TG_SERVER)
        api.requests = Mock()
        api.requests.post.return_value.json.return_value = {"ok": True}
        results = [{"id": "1", "type": "video", "video_file_id": "file-id", "title": "Видео"}]

        response = api.answer_inline_query(
            "query-id",
            results,
            cache_time=0,
            next_offset="photos",
            is_personal=True,
        )

        method, params = api.requests.post.call_args.args
        self.assertEqual(method, "answerInlineQuery")
        self.assertEqual(params["inline_query_id"], "query-id")
        self.assertEqual(json.loads(params["results"]), results)
        self.assertEqual(params["next_offset"], "photos")
        self.assertIs(params["is_personal"], True)
        self.assertEqual(response, {"ok": True})
