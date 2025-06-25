from apps.bot.api.handler import API
from apps.bot.api.imgdb import ImgdbAPI
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def get_text_for_images_in_body(images: list[PhotoAttachment], log_filter=None) -> str:
        result = []
        i_api = ImgdbAPI(log_filter=log_filter)
        for image in images:
            image_url = i_api.upload_image(image, expire=60)
            result.append(f"![image]({image_url})")
        return "\n" + "\n".join(result)
