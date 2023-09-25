import json
import logging

import requests

from apps.bot.classes.const.exceptions import PError
from petrovich.settings import env

logger = logging.getLogger('bot')


class Github:
    REPO_OWNER = 'Xoma163'
    REPO_NAME = 'petrovich'
    ISSUES_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues'
    LABELS_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/labels'
    TOKEN = env.str('GITHUB_TOKEN')
    HEADERS = {
        "Authorization": f"token {TOKEN}"
    }

    def create_issue(self, title, body=None, assignee=None, milestone=None, labels=None):
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

        r = requests.post(self.ISSUES_URL, json.dumps(issue_data), headers=self.HEADERS)
        r_json = r.json()
        logger.debug({"response": r_json})

        if r.status_code != 201:
            raise PError("Не удалось создать issue на github")
        return r_json

    def delete_issue(self, _id):
        issue_data = {
            "state": "closed",
            "labels": ["Не пофикшу"]
        }
        r = requests.post(f"{self.ISSUES_URL}/{_id}", json.dumps(issue_data), headers=self.HEADERS)
        r_json = r.json()
        logger.debug({"response": r_json})

        if r.status_code != 200:
            raise PError("Не удалось закрыть issue на github")
        return r_json

    def get_all_labels(self):
        r = requests.get(self.LABELS_URL, json.dumps({}), headers=self.HEADERS).json()
        logger.debug({"response": r})
        return [x['name'] for x in r]
