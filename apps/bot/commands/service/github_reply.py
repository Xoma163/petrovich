import re

from apps.bot.api.github.issue import GithubIssueAPI
from apps.bot.classes.command import Command
from apps.bot.classes.event.event import Event
from apps.bot.classes.messages.attachments.photo import PhotoAttachment
from apps.bot.classes.messages.response_message import ResponseMessage, ResponseMessageItem
from apps.bot.utils.utils import get_admin_profile


class GithubReply(Command):
    BODY_FINE_PRINT_TEMPLATE = "Комментарий от пользователя {sender} (id={id})\n" \
                               "Данный комментарий сгенерирован автоматически"
    ACCEPT_PATTERN = r"Новый комментарий от разработчика под вашей проблемой #(\d{3,5})\n"

    NEW_COMMENT_FROM_USER_TEMPLATE = "Новый комментарий от пользователей под {problem_str}\n\n{comment}"

    # Обоснование: это служебная команда должна откликаться только на реплаи на определённый комментарий
    priority = 95

    def accept(self, event: Event) -> bool:
        if event.fwd and event.fwd[0].message:
            return bool(re.findall(self.ACCEPT_PATTERN, event.fwd[0].message.clear_case))
        return False

    def start(self) -> ResponseMessage | None:
        issue_number = re.search(self.ACCEPT_PATTERN, self.event.fwd[0].message.clear_case).group(1)
        issue = GithubIssueAPI()
        issue.number = issue_number
        issue.get_from_github()

        body = []
        comment = self.event.message.raw
        if comment:
            body.append(comment)

        error_msg = None
        photos = self.event.get_all_attachments([PhotoAttachment], use_fwd=False)
        if photos:
            body.append(issue.get_text_for_images_in_body(photos, log_filter=self.event.log_filter))

        body.append(self.BODY_FINE_PRINT_TEMPLATE.format(sender=self.event.sender, id=self.event.sender.pk))
        body = "\n\n".join(body)
        issue.add_comment(body)

        if not comment and photos:
            comment = "Изображение(я)"
        self.send_comment_info_to_admin(issue, comment)
        answer = "Успешно оставил ваш комментарий"
        if error_msg:
            answer += f"\n{error_msg}"
        return ResponseMessage(ResponseMessageItem(text=answer))

    def send_comment_info_to_admin(self, issue: GithubIssueAPI, comment):
        profile = get_admin_profile(exclude_profile=issue.author)
        if not profile:
            return

        problem_str = self.bot.get_formatted_url('проблемой #' + str(issue.number), issue.remote_url)
        answer = self.NEW_COMMENT_FROM_USER_TEMPLATE.format(problem_str=problem_str, comment=comment)
        rmi = ResponseMessageItem(answer)
        rmi.peer_id = profile.get_tg_user().user_id
        self.bot.send_response_message_item(rmi)
