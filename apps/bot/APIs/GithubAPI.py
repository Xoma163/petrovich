import json

import requests

from apps.bot.classes.Exceptions import PError
from petrovich.settings import env

REPO_OWNER = 'Xoma163'
REPO_NAME = 'petrovich'


class GithubAPI:
    def __init__(self):
        pass

    @staticmethod
    def create_issue(title, body=None, assignee=None, milestone=None, labels=None):
        """Создание issue."""
        if labels is None:
            labels = []

        url = 'https://api.github.com/repos/%s/%s/issues' % (REPO_OWNER, REPO_NAME)
        issue = {
            'title': title,
            'body': body,
            'assignee': assignee,
            'milestone': milestone,
            'labels': labels
        }
        headers = {"Authorization": f"token {env.str('GITHUB_TOKEN')}"}

        r = requests.post(url, json.dumps(issue), headers=headers)
        if r.status_code != 201:
            raise PError("Не удалось создать issue на github")
        return r.json()
