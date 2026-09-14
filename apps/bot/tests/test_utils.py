from unittest.mock import MagicMock, Mock, patch

from django.test import SimpleTestCase

from apps.bot.utils import get_profile_by_name


class GetProfileByNameTests(SimpleTestCase):
    @patch("apps.bot.utils.Profile.objects")
    def test_searches_by_telegram_username_without_at_sign(self, profile_objects):
        queryset = MagicMock()
        profile = Mock()
        profile_objects.all.return_value = queryset
        queryset.filter.return_value = queryset
        queryset.distinct.return_value = queryset
        queryset.__len__.return_value = 1
        queryset.first.return_value = profile

        result = get_profile_by_name(["@telegram_user"])

        lookup = queryset.filter.call_args.args[0]
        self.assertIn(
            ("user__nickname__icontains", "telegram_user"),
            lookup.children[-1].children,
        )
        queryset.distinct.assert_called_once_with()
        self.assertIs(result, profile)
