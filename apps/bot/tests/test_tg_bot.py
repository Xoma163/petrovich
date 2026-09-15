from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.attachments.sticker import StickerAttachment
from apps.bot.core.messages.response_message import ResponseMessageItem


class TgBotAttachmentRoutingTestCase(SimpleTestCase):
    @patch("apps.bot.core.bot.telegram.tg_bot.ChatActionSender")
    def test_sticker_attachment_is_sent(self, chat_action_sender):
        bot = TgBot.__new__(TgBot)
        send_sticker = Mock(return_value={"ok": True})
        bot.att_map = {StickerAttachment: send_sticker}
        sticker = StickerAttachment()
        sticker.file_id = "sticker-file-id"
        rmi = ResponseMessageItem(text="caption", attachments=[sticker], peer_id=123)

        result = bot._send_response_message_item(rmi)

        chat_action_sender.assert_called_once_with(bot, ChatActionEnum.CHOOSE_STICKER, 123, None)
        send_sticker.assert_called_once_with(rmi)
        self.assertEqual(result, {"ok": True})


class TgBotInlineRoutingTestCase(SimpleTestCase):
    @patch("apps.bot.core.bot.telegram.tg_bot.Meme")
    def test_inline_offset_and_next_offset_are_forwarded(self, meme_command):
        bot = TgBot.__new__(TgBot)
        bot.api_handler = Mock()
        bot.api_handler.answer_inline_query.return_value = {"ok": True}
        results = [{"id": "1", "type": "photo", "photo_file_id": "file-id"}]
        meme_command.return_value.get_tg_inline_memes.return_value = (results, "gifs")
        event = Mock()
        event.inline_data = {
            "id": "query-id",
            "offset": "photos",
            "message": Mock(clear="привет"),
        }

        response = bot.route_inline_mode(event)

        meme_command.return_value.get_tg_inline_memes.assert_called_once_with(["привет"], offset="photos")
        bot.api_handler.answer_inline_query.assert_called_once_with(
            inline_query_id="query-id",
            results=results,
            cache_time=0,
            next_offset="gifs",
            is_personal=True,
        )
        self.assertEqual(response, {"ok": True})
