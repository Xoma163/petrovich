from apps.bot.api.handler import API
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

    def get_text_for_images_in_body(self, images: list[PhotoAttachment]) -> str:
        result = []
        for image in images:
            from apps.bot.api.imgur import Imgur
            i_api = Imgur(log_filter=self.event.log_filter)
            image_url = i_api.upload_image(image.download_content())
            result.append(f"![image]({image_url})")
        return "\n" + "\n".join(result)
