import json
import re
from typing import Optional

from requests import HTTPError

from apps.bot.api.github.github import GithubAPI
from apps.bot.classes.const.exceptions import PWarning
from apps.bot.models import Profile


class GithubIssueAPI(GithubAPI):
    USER_PK_RE = re.compile(r"Ишю от пользователя .* \(id=(.*)\)")
    NO_FIX_LABEL = 'Не пофикшу'

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

        self.author: Optional[Profile] = None

    def parse_response(self, response: dict):
        self.id: str = response['id']
        self.number: str = response['number']
        self.title: str = response['title']
        self.labels: list[str] = [x['name'] for x in response['labels']]
        self.body: str = response['body']
        self.assignee: str = response['assignee']
        self.remote_url: str = response['html_url']

        self.author: Optional[Profile] = None
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
    def has_no_fix_label(self):
        return any(x for x in self.labels if x == self.NO_FIX_LABEL)
