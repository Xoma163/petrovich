import json
import re
from datetime import datetime

from requests import HTTPError

from apps.bot.api.github.github import GithubAPI
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.models import Profile


class GithubIssueAPI(GithubAPI):
    USER_PK_RE = re.compile(r"Ишю от пользователя .* \(id=(.*)\)")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.requests.headers = self.HEADERS

        self.id: str = ""
        self.number: str = ""
        self.title: str = ""
        self.labels: list[str] = []
        self.body: str = ""
        self.assignee: str = ""

        self.remote_url: str = ""
        self.created_at: datetime | None = None
        self.state_reason: str | None = None
        self.author: Profile | None = None

    def parse_response(self, response: dict):
        self.id: str = response['id']
        self.number: str = response['number']
        self.title: str = response['title']
        self.labels: list[str] = [x['name'] for x in response['labels']]
        self.body: str = response['body']
        self.assignee: str = response['assignee']
        self.remote_url: str = response['html_url']
        self.created_at: datetime = datetime.strptime(response['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        self.state_reason: str = response['state_reason']

        self.author: Profile | None = None
        match = self.USER_PK_RE.findall(self.body)
        if match:
            profile_pk = match[-1]
            try:
                self.author = Profile.objects.get(pk=profile_pk)
            except Profile.DoesNotExist:
                self.author = None

    def get_from_github(self):
        r = self.requests.post(f"{self.ISSUES_URL}/{self.number}")
        try:
            r.raise_for_status()
        except HTTPError:
            raise PWarning(f"Не удалось найти issue с id {self.number} на github")
        r_json = r.json()
        self.parse_response(r_json)

    def create_in_github(self):
        """Создание issue."""

        issue_data = {
            'title': self.title,
            'body': self.body,
            'assignee': self.assignee,
            'labels': self.labels
        }

        r = self.requests.post(self.ISSUES_URL, json.dumps(issue_data))
        r_json = r.json()

        try:
            r.raise_for_status()
        except HTTPError:
            raise PWarning("Проблема с созданием issue на github")

        self.remote_url = r_json['html_url']

    def add_comment(self, comment: str):
        """Добавление комментария."""

        comment_data = {
            'body': comment
        }
        COMMENT_URL = f"{self.ISSUES_URL}/{self.number}/comments"
        r = self.requests.post(COMMENT_URL, json.dumps(comment_data))

        try:
            r.raise_for_status()
        except HTTPError:
            raise PWarning("Проблема с созданием комментария на github")

    def delete_in_github(self) -> dict:
        issue_data = {
            "state": "closed",
            "labels": self.labels + ["Не пофикшу"]
        }
        r = self.requests.post(f"{self.ISSUES_URL}/{self.number}", json.dumps(issue_data))

        try:
            r.raise_for_status()
        except HTTPError:
            raise PWarning("Проблема с удалением issue на github")

        r_json = r.json()
        return r_json

    def get_all_labels(self) -> list[str]:
        r = self.requests.get(self.LABELS_URL, json.dumps({})).json()
        return [x['name'] for x in r]

    @property
    def state_reason_is_not_planned(self) -> bool:
        return self.state_reason == "not_planned"
