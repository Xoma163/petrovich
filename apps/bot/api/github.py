import json
from typing import List

from apps.bot.api.handler import API
from apps.bot.classes.const.exceptions import PError
from petrovich.settings import env


class Github(API):
    REPO_OWNER = 'Xoma163'
    REPO_NAME = 'petrovich'
    ISSUES_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues'
    LABELS_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/labels'
    TOKEN = env.str('GITHUB_TOKEN')
    HEADERS = {
        "Authorization": f"token {TOKEN}"
    }

    def create_issue(self, title, body=None, assignee=None, milestone=None, labels=None) -> dict:
        """Создание issue."""
        if labels is None:
            labels = []

        issue_data = {
            'title': title,
            'body': body,
            'assignee': assignee,
            'milestone': milestone,
            'labels': labels
        }

        r = self.requests.post(self.ISSUES_URL, json.dumps(issue_data), headers=self.HEADERS)
        r_json = r.json()

        if r.status_code != 201:
            raise PError("Не удалось создать issue на github")
        return r_json

    def delete_issue(self, _id) -> dict:
        issue_data = {
            "state": "closed",
            "labels": ["Не пофикшу"]
        }
        r = self.requests.post(f"{self.ISSUES_URL}/{_id}", json.dumps(issue_data), headers=self.HEADERS)
        r_json = r.json()

        if r.status_code != 200:
            if r.status_code == 404:
                raise PError(f"Иша с id {_id} не найдена")
            raise PError("Не удалось закрыть issue на github")
        return r_json

    def get_all_labels(self) -> List[str]:
        r = self.requests.get(self.LABELS_URL, json.dumps({}), headers=self.HEADERS).json()
        return [x['name'] for x in r]
