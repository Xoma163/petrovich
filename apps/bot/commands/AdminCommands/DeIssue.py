from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import Issue


class DeIssue(CommonCommand):
    def __init__(self):
        names = ["деишю", "деишью", "хуишю", "хуишью"]
        help_text = "Хуишью - удаляет последнюю добавленную проблему"
        super().__init__(names, help_text, access=Role.ADMIN)

    def start(self):
        issue = Issue.objects.last()
        if not issue:
            return "Нет ишюс!"
        issue_text = issue.text
        issue.delete()
        return f'Ишю удалено:\n{issue_text}'
