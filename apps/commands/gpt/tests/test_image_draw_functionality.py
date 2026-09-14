from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.commands.gpt.commands_utils.gpt.functionality.image_draw import GPTImageDrawFunctionality
from apps.commands.gpt.models import ImageDrawModel
from apps.shared.exceptions import PWarning


class TestableImageDrawFunctionality(GPTImageDrawFunctionality):
    pass


class ImageDrawFunctionalityTests(SimpleTestCase):
    def make_command(self, keys: set[str], model: ImageDrawModel) -> TestableImageDrawFunctionality:
        command = TestableImageDrawFunctionality()
        command.get_image_draw_model = lambda: model
        command.event = SimpleNamespace(
            message=SimpleNamespace(
                keys=keys,
                is_key_provided=lambda available_keys: bool(keys & available_keys),
            )
        )
        return command

    def make_model(self, *, supported_qualities=None) -> ImageDrawModel:
        return ImageDrawModel(
            name="gpt-image-test",
            width=1024,
            height=1024,
            quality="medium",
            supported_qualities=supported_qualities or ["low", "medium", "high", "xhigh", "max"],
            supported_sizes=["1024x1024", "1536x1024", "1024x1536"],
        )

    def test_uses_model_defaults_without_parameter_keys(self):
        selected = self.make_command(set(), self.make_model()).get_image_draw_model_with_parameters()

        self.assertEqual(selected.quality, "medium")
        self.assertEqual(selected.size, "1024x1024")

    def test_selects_max_quality_and_portrait_size(self):
        selected = self.make_command(
            {"max", "портрет"},
            self.make_model(),
        ).get_image_draw_model_with_parameters()

        self.assertEqual(selected.quality, "max")
        self.assertEqual(selected.size, "1024x1536")

    def test_rejects_quality_unsupported_by_model(self):
        command = self.make_command(
            {"max"},
            self.make_model(supported_qualities=["low", "medium", "high"]),
        )

        with self.assertRaisesMessage(PWarning, 'не поддерживает качество "max"'):
            command.get_image_draw_model_with_parameters()

    def test_rejects_zero_images(self):
        command = self.make_command({"0"}, self.make_model())

        with self.assertRaisesMessage(PWarning, "Минимальное число изображений"):
            command._get_images_count_by_keys()
