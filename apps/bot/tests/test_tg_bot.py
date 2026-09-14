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
