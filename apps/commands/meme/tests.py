from types import SimpleNamespace

from django.test import TestCase

from apps.bot.core.messages.attachments.gif import AnimationAttachment
from apps.bot.core.messages.attachments.photo import PhotoAttachment
from apps.bot.core.messages.attachments.video import VideoAttachment
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

        results, next_offset = self._get_command().get_tg_inline_memes(["ебать"])

        self.assertEqual(
            results[0],
            {"id": str(meme.pk), "type": "gif", "gif_file_id": "legacy-gif-file-id", "title": meme.name},
        )
        self.assertEqual(next_offset, "")

    def test_exact_search_converts_animation_to_telegram_gif_type(self):
        meme = Meme.objects.create(
            name="анимация",
            type=AnimationAttachment.TYPE,
            approved=True,
            tg_file_id="animation-file-id",
        )

        results, next_offset = self._get_command().get_tg_inline_memes(["анимация"])

        self.assertEqual(
            results[0],
            {"id": str(meme.pk), "type": "gif", "gif_file_id": "animation-file-id", "title": meme.name},
        )
        self.assertEqual(next_offset, "")

    def test_mixed_results_are_split_into_video_then_photo_pages(self):
        video = Meme.objects.create(
            name="привет видео",
            type=VideoAttachment.TYPE,
            approved=True,
            tg_file_id="video-file-id",
        )
        photo = Meme.objects.create(
            name="привет фото",
            type=PhotoAttachment.TYPE,
            approved=True,
            tg_file_id="photo-file-id",
        )
        command = self._get_command()

        first_page, next_offset = command.get_tg_inline_memes(["привет"])
        second_page, final_offset = command.get_tg_inline_memes(["привет"], offset=next_offset)

        self.assertEqual([result["id"] for result in first_page], [str(video.pk)])
        self.assertEqual([result["type"] for result in first_page], ["video"])
        self.assertEqual(next_offset, "photos")
        self.assertEqual([result["id"] for result in second_page], [str(photo.pk)])
        self.assertEqual([result["type"] for result in second_page], ["photo"])
        self.assertEqual(final_offset, "")

    def test_photo_page_is_first_when_no_videos_match(self):
        photo = Meme.objects.create(
            name="кря",
            type=PhotoAttachment.TYPE,
            approved=True,
            tg_file_id="photo-file-id",
        )

        results, next_offset = self._get_command().get_tg_inline_memes(["кря"])

        self.assertEqual([result["id"] for result in results], [str(photo.pk)])
        self.assertEqual(next_offset, "")

    def test_search_has_ten_results_total_across_media_pages(self):
        videos = [
            Meme.objects.create(
                name=f"привет видео {index}",
                type=VideoAttachment.TYPE,
                approved=True,
                tg_file_id=f"video-{index}",
                uses=20 - index,
            )
            for index in range(9)
        ]
        photo = Meme.objects.create(
            name="привет фото",
            type=PhotoAttachment.TYPE,
            approved=True,
            tg_file_id="photo",
            uses=10,
        )
        Meme.objects.create(
            name="привет лишнее видео",
            type=VideoAttachment.TYPE,
            approved=True,
            tg_file_id="extra-video",
            uses=1,
        )
        command = self._get_command()

        first_page, next_offset = command.get_tg_inline_memes(["привет"], max_count=50)
        second_page, final_offset = command.get_tg_inline_memes(["привет"], max_count=50, offset=next_offset)

        self.assertEqual([result["id"] for result in first_page], [str(video.pk) for video in videos])
        self.assertEqual(next_offset, "photos")
        self.assertEqual([result["id"] for result in second_page], [str(photo.pk)])
        self.assertEqual(final_offset, "")
        self.assertEqual(len(first_page) + len(second_page), 10)

    def test_exact_match_stays_in_first_ten_results(self):
        for index in range(10):
            Meme.objects.create(
                name=f"привет {index}",
                type=VideoAttachment.TYPE,
                approved=True,
                tg_file_id=f"video-{index}",
                uses=10,
            )
        exact = Meme.objects.create(
            name="привет",
            type=PhotoAttachment.TYPE,
            approved=True,
            tg_file_id="exact-photo",
        )

        first_page, next_offset = self._get_command().get_tg_inline_memes(["привет"])
        second_page, final_offset = self._get_command().get_tg_inline_memes(["привет"], offset=next_offset)

        self.assertEqual(len(first_page), 9)
        self.assertEqual(next_offset, "photos")
        self.assertEqual([result["id"] for result in second_page], [str(exact.pk)])
        self.assertEqual(final_offset, "")

    def test_empty_search_is_also_limited_to_ten_results(self):
        for index in range(11):
            Meme.objects.create(
                name=f"мем {index}",
                type=PhotoAttachment.TYPE,
                approved=True,
                tg_file_id=f"photo-{index}",
            )

        results, next_offset = self._get_command().get_tg_inline_memes([])

        self.assertEqual(len(results), 10)
        self.assertEqual(next_offset, "")
