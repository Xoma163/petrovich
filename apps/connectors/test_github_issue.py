from unittest.mock import patch

from django.test import SimpleTestCase

from apps.connectors.api.github.issue import GithubIssueAPI


class GithubIssueParsingTests(SimpleTestCase):
    def test_footer_matches_numeric_id_on_its_own_line(self):
        body = "Description\nИшю от пользователя User (extra text) (id=42)\r\nGenerated automatically"
        self.assertEqual(GithubIssueAPI.USER_PK_RE.findall(body), ["42"])

    def test_non_footer_and_invalid_id_do_not_match(self):
        for body in (
            "quoted Ишю от пользователя User (id=42)",
            "Ишю от пользователя User (id=not-a-number)",
            "Ишю от пользователя User (id=42) extra text",
            "Ишю от пользователя " + " (id=" * 10000,
        ):
            with self.subTest(length=len(body)):
                self.assertEqual(GithubIssueAPI.USER_PK_RE.findall(body), [])

    @patch("apps.connectors.api.github.issue.Profile.objects.get")
    def test_null_body_has_no_author(self, get_profile):
        issue = GithubIssueAPI(log_filter=None)
        issue.parse_response({
            "id": 1, "number": 1, "title": "Title", "labels": [], "body": None,
            "assignee": None, "html_url": "https://github.com/example/repo/issues/1",
            "created_at": "2026-11-16T00:00:00Z", "state_reason": None,
        })
        self.assertEqual(issue.body, "")
        self.assertIsNone(issue.author)
        get_profile.assert_not_called()

    @patch("apps.connectors.api.github.issue.Profile.objects.get")
    def test_last_footer_selects_author(self, get_profile):
        issue = GithubIssueAPI(log_filter=None)
        issue.parse_response({
            "id": 1, "number": 1, "title": "Title", "labels": [],
            "body": "Ишю от пользователя First (id=1)\nИшю от пользователя Second (id=2)",
            "assignee": None, "html_url": "https://github.com/example/repo/issues/1",
            "created_at": "2026-11-16T00:00:00Z", "state_reason": None,
        })
        get_profile.assert_called_once_with(pk="2")
        self.assertIs(issue.author, get_profile.return_value)
