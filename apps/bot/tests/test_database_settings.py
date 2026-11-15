import os
import runpy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured


class DatabaseSettingsTests(TestCase):
    def load_database(self, **variables):
        environment = {
            "SECRET_KEY": "isolated-settings-test",
            "DEBUG": "False",
            "MINECRAFT_DOMAIN": "example.invalid",
            "PETROVICH_DOMAIN": "example.invalid",
            "ALLOWED_HOSTS": "localhost",
            "REDIS_URL": "redis://127.0.0.1:1/0",
            "SENTRY_URL": "",
            **variables,
        }
        settings_file = Path(__file__).resolve().parents[3] / "petrovich/settings.py"
        with (
            patch("sentry_sdk.init"),
            patch.dict(os.environ, environment, clear=True),
            patch("environ.Env.read_env"),
        ):
            return runpy.run_path(str(settings_file))["DATABASES"]["default"]

    def test_password_placeholder_handles_url_special_characters(self):
        password = "$test:@/#?%+ ${literal} пароль"
        database = self.load_database(
            DATABASE_URL="postgres://petrovich:${POSTGRES_PASSWORD}@127.0.0.1:15433/petrovich",
            POSTGRES_PASSWORD=password,
        )

        self.assertEqual(database["PASSWORD"], password)
        self.assertEqual(database["HOST"], "127.0.0.1")
        self.assertEqual(database["PORT"], 15433)
        self.assertEqual(database["NAME"], "petrovich")

    def test_complete_url_does_not_require_separate_password(self):
        database = self.load_database(DATABASE_URL="postgres://test:legacy%40value@localhost/example")

        self.assertEqual(database["PASSWORD"], "legacy@value")

    def test_missing_referenced_password_fails(self):
        with self.assertRaises(ImproperlyConfigured):
            self.load_database(DATABASE_URL="postgres://test:${POSTGRES_PASSWORD}@localhost/example")

    def test_default_database_url_remains_supported(self):
        self.assertEqual(self.load_database()["NAME"], "petrovich")

    def test_empty_referenced_password_fails(self):
        with self.assertRaises(ImproperlyConfigured):
            self.load_database(
                DATABASE_URL="postgres://test:${POSTGRES_PASSWORD}@localhost/example",
                POSTGRES_PASSWORD="",
            )
