from types import SimpleNamespace
from unittest.mock import Mock

from django.test import TestCase

from apps.commands.gpt.api.providers.chatgpt import ChatGPTAPI
from apps.commands.gpt.commands_utils.gpt.mixins.model_choice import GPTModelChoiceMixin
from apps.commands.gpt.models import (
    CompletionsModel,
    ImageDrawModel,
    Provider,
    VisionModel,
    VoiceRecognitionModel,
)


class ModelChoiceBot:
    @staticmethod
    def get_formatted_text(text):
        return text

    @staticmethod
    def get_formatted_text_line(text):
        return text

    @staticmethod
    def get_button(*args, **kwargs):
        return {"args": args, "kwargs": kwargs}

    @staticmethod
    def get_inline_keyboard(buttons):
        return buttons


class ModelChoiceCommand(GPTModelChoiceMixin):
    name = "gpt"

    def __init__(self, provider, settings):
        self.provider_model = provider
        self.provider = SimpleNamespace(api_class=ChatGPTAPI, type_enum=SimpleNamespace(value="ChatGPT"))
        self.settings = settings
        self.bot = ModelChoiceBot()
        self.event = SimpleNamespace(message=SimpleNamespace(args=[]))

    def get_profile_gpt_settings(self):
        return self.settings


class GPTModelChoiceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.provider = Provider.objects.create(name="chatgpt")
        cls.other_provider = Provider.objects.create(name="deepseek")

        cls.completions_model = cls._create_completions_model(cls.provider, "shared-model")
        cls.vision_model = cls._create_vision_model(cls.provider, "shared-model")
        cls.image_draw_model = ImageDrawModel.objects.create(
            provider=cls.provider,
            name="shared-model",
            width=1024,
            height=1024,
            quality="medium",
        )
        cls.voice_model = VoiceRecognitionModel.objects.create(
            provider=cls.provider,
            name="shared-model",
            voice_recognition_1_min_cost=1,
        )

        cls._create_completions_model(cls.other_provider, "shared-model")
        cls._create_vision_model(cls.other_provider, "shared-model")
        ImageDrawModel.objects.create(
            provider=cls.other_provider,
            name="shared-model",
            width=1024,
            height=1024,
            quality="medium",
        )
        VoiceRecognitionModel.objects.create(
            provider=cls.other_provider,
            name="shared-model",
            voice_recognition_1_min_cost=1,
        )

    @staticmethod
    def _create_completions_model(provider, name):
        return CompletionsModel.objects.create(
            provider=provider,
            name=name,
            input_1m_token_cost=1,
            input_cached_1m_token_cost=1,
            output_1m_token_cost=1,
            web_search_1k_token_cost=1,
        )

    @staticmethod
    def _create_vision_model(provider, name):
        return VisionModel.objects.create(
            provider=provider,
            name=name,
            input_1m_token_cost=1,
            input_cached_1m_token_cost=1,
            output_1m_token_cost=1,
            web_search_1k_token_cost=1,
        )

    @staticmethod
    def _make_settings():
        return SimpleNamespace(
            completions_model=None,
            vision_model=None,
            image_draw_model=None,
            voice_recognition_model=None,
            save=Mock(),
        )

    def test_each_model_type_is_selected_from_current_provider(self):
        settings = self._make_settings()
        command = ModelChoiceCommand(self.provider, settings)
        choices = [
            ("completions", command._sub_menu_completions_model_choice, "completions_model", self.completions_model),
            ("vision", command._sub_menu_vision_model_choice, "vision_model", self.vision_model),
            ("draw", command._sub_menu_image_draw_model_choice, "image_draw_model", self.image_draw_model),
            ("voice", command._sub_menu_voice_recognition_model_choice, "voice_recognition_model", self.voice_model),
        ]

        for alias, method, settings_field, expected_model in choices:
            with self.subTest(alias=alias):
                settings.save.reset_mock()
                command.event.message.args = ["модель", alias, "shared-model"]
                method(settings)
                self.assertEqual(getattr(settings, settings_field), expected_model)
                settings.save.assert_called_once_with()

    def test_each_model_type_can_be_reset(self):
        settings = self._make_settings()
        command = ModelChoiceCommand(self.provider, settings)
        choices = [
            ("completions", command._sub_menu_completions_model_choice, "completions_model"),
            ("vision", command._sub_menu_vision_model_choice, "vision_model"),
            ("draw", command._sub_menu_image_draw_model_choice, "image_draw_model"),
            ("voice", command._sub_menu_voice_recognition_model_choice, "voice_recognition_model"),
        ]

        for alias, method, settings_field in choices:
            with self.subTest(alias=alias):
                settings.save.reset_mock()
                setattr(settings, settings_field, object())
                command.event.message.args = ["модель", alias, "сброс"]
                method(settings)
                self.assertIsNone(getattr(settings, settings_field))
                settings.save.assert_called_once_with()

    def test_models_list_marks_selected_model_of_its_own_type(self):
        settings = self._make_settings()
        settings.image_draw_model = self.image_draw_model
        command = ModelChoiceCommand(self.provider, settings)

        sections = command._get_models_list_of_str()
        image_section = next(section for section in sections if "генерации изображений" in section)
        completions_section = next(section for section in sections if "обработки текста" in section)

        self.assertIn("shared-model", image_section)
        self.assertIn("1024x1024", image_section)
        self.assertIn("выбрано", image_section)
        self.assertNotIn("выбрано", completions_section)

    def test_models_list_handles_supported_type_without_models(self):
        empty_provider = Provider.objects.create(name="google")
        command = ModelChoiceCommand(empty_provider, self._make_settings())

        sections = command._get_models_list_of_str()

        self.assertEqual(len(sections), 4)
        self.assertTrue(all(section.endswith("пуст") for section in sections))
