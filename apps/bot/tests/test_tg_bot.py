from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from apps.bot.core.bot.telegram.tg_bot import TgBot
from apps.bot.core.chat_actions import ChatActionEnum
from apps.bot.core.messages.attachments.photo import PhotoAttachment
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


class TgBotLinkPreviewTestCase(SimpleTestCase):
    def test_preview_setting_is_forwarded(self):
        for disabled in (None, False, True):
            with self.subTest(disabled=disabled):
                bot = TgBot.__new__(TgBot)
                bot.api_handler = Mock()
                rmi = ResponseMessageItem(
                    text="Источник: https://example.com", peer_id=123, disable_web_page_preview=disabled
                )

                bot.send_message(rmi)

                self.assertIs(bot.api_handler.send_message.call_args.kwargs["disable_web_page_preview"], disabled)

    def test_preview_is_disabled_for_all_text_chunks(self):
        bot = TgBot.__new__(TgBot)
        bot.api_handler = Mock()
        rmi = ResponseMessageItem(text="a " * 5000, peer_id=123, disable_web_page_preview=True)

        bot._send_response_message_item(rmi)

        self.assertGreater(bot.api_handler.send_message.call_count, 1)
        for call in bot.api_handler.send_message.call_args_list:
            self.assertIs(call.kwargs["disable_web_page_preview"], True)

    def test_rich_message_keeps_supported_payload(self):
        bot = TgBot.__new__(TgBot)
        bot.api_handler = Mock()
        markdown = "Источник: [example](https://example.com)"
        rmi = ResponseMessageItem(text=markdown, rich_markdown=markdown, disable_web_page_preview=True)

        bot.send_message(rmi)

        bot.api_handler.send_message.assert_not_called()
        self.assertEqual(bot.api_handler.send_rich_message.call_args.kwargs["rich_message"], {"markdown": markdown})

    @patch("apps.bot.core.bot.telegram.tg_bot.ChatActionSender")
    def test_album_source_text_disables_preview(self, chat_action_sender):
        bot = TgBot.__new__(TgBot)
        bot.api_handler = Mock()
        bot._send_media_group = Mock(return_value={"ok": True})
        rmi = ResponseMessageItem(
            text='Источник: <a href="https://example.com">example</a>',
            attachments=[PhotoAttachment(), PhotoAttachment()],
            peer_id=123,
            disable_web_page_preview=True,
        )

        bot._send_response_message_item(rmi)

        bot._send_media_group.assert_called_once_with(rmi)
        bot.api_handler.send_message.assert_called_once()
        self.assertIs(bot.api_handler.send_message.call_args.kwargs["disable_web_page_preview"], True)
        self.assertIn("Источник:", bot.api_handler.send_message.call_args.kwargs["text"])
