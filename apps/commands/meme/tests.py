from types import SimpleNamespace

from django.test import TestCase

from apps.bot.core.messages.attachments.gif import AnimationAttachment
from apps.commands.meme.commands.meme import Meme as MemeCommand
from apps.commands.meme.models import Meme


class MemeInlineSearchTestCase(TestCase):
    @staticmethod
    def _get_command():
        sender = SimpleNamespace(check_role=lambda role: False)
        event = SimpleNamespace(sender=sender)
        return MemeCommand(event=event)

    def test_exact_search_supports_legacy_gif_type(self):
        meme = Meme.objects.create(name="ебать", type="gif", approved=True, tg_file_id="legacy-gif-file-id")

        results = self._get_command().get_tg_inline_memes(["ебать"])

        self.assertEqual(
            results[0],
            {"id": str(meme.pk), "type": "gif", "gif_file_id": "legacy-gif-file-id", "title": meme.name},
        )

    def test_exact_search_converts_animation_to_telegram_gif_type(self):
        meme = Meme.objects.create(
            name="анимация",
            type=AnimationAttachment.TYPE,
            approved=True,
            tg_file_id="animation-file-id",
        )

        results = self._get_command().get_tg_inline_memes(["анимация"])

        self.assertEqual(
            results[0],
            {"id": str(meme.pk), "type": "gif", "gif_file_id": "animation-file-id", "title": meme.name},
        )
