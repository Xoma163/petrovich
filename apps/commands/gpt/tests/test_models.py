from django.db import IntegrityError
from django.test import TestCase

from apps.commands.gpt.models import CompletionsModel, Provider


class CompletionsModelDefaultTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.provider = Provider.objects.create(name="chatgpt")

    def create_model(self, name: str, *, is_default: bool) -> CompletionsModel:
        return CompletionsModel.objects.create(
            provider=self.provider,
            name=name,
            is_default=is_default,
            input_1m_token_cost=1,
            input_cached_1m_token_cost=1,
            output_1m_token_cost=1,
            web_search_1k_token_cost=1,
        )

    def test_adding_default_model_clears_previous_default(self):
        previous_default = self.create_model("previous", is_default=True)

        new_default = self.create_model("new", is_default=True)

        previous_default.refresh_from_db()
        self.assertFalse(previous_default.is_default)
        self.assertTrue(new_default.is_default)

    def test_updating_model_to_default_clears_previous_default(self):
        previous_default = self.create_model("previous", is_default=True)
        new_default = self.create_model("new", is_default=False)

        new_default.is_default = True
        new_default.save()

        previous_default.refresh_from_db()
        new_default.refresh_from_db()
        self.assertFalse(previous_default.is_default)
        self.assertTrue(new_default.is_default)

    def test_failed_new_default_save_restores_previous_default(self):
        previous_default = self.create_model("duplicate", is_default=True)
        new_default = self.create_model("new", is_default=False)
        new_default.name = "duplicate"
        new_default.is_default = True

        with self.assertRaises(IntegrityError):
            new_default.save()

        previous_default.refresh_from_db()
        self.assertTrue(previous_default.is_default)
