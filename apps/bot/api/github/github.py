from apps.bot.api.handler import API
from petrovich.settings import env


class GithubAPI(API):
    TOKEN = env.str('GITHUB_TOKEN')
    HEADERS = {
        "Authorization": f"token {TOKEN}"
    }

    REPO_OWNER = 'Xoma163'
    REPO_NAME = 'petrovich'

    BASE_API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

    ISSUES_URL = f'{BASE_API_URL}/issues'
    LABELS_URL = f'{BASE_API_URL}/labels'
