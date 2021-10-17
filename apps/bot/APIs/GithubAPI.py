import json

import requests

from apps.bot.classes.consts.Exceptions import PError
from petrovich.settings import env


class GithubAPI:
    REPO_OWNER = 'Xoma163'
    REPO_NAME = 'petrovich'
    ISSUES_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues'
    TOKEN = env.str('GITHUB_TOKEN')
    HEADERS = {"Authorization": f"token {TOKEN}"}

    def __init__(self):
        pass

    def create_issue(self, title, body=None, assignee=None, milestone=None, labels=None):
        """Создание issue."""
        if labels is None:
            labels = []

        issue = {
            'title': title,
            'body': body,
            'assignee': assignee,
            'milestone': milestone,
            'labels': labels
        }

        r = requests.post(self.ISSUES_URL, json.dumps(issue), headers=self.HEADERS)
        if r.status_code != 201:
            raise PError("Не удалось создать issue на github")
        return r.json()
