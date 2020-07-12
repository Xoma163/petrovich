from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import Issue as IssueModel

# ToDo: TG
class Issue(CommonCommand):
    def __init__(self):
        names = ["баг", "ошибка", "ишю", "ишью"]
        help_text = "Баг - добавляет проблему Петровича, которую нужно решить"
        detail_help_text = "Баг (текст/пересланные сообщения) - добавляет проблему Петровича, которую нужно решить"
        super().__init__(names, help_text, detail_help_text, api=False, enabled=False)

    def start(self):
        msgs = self.event.fwd
        if not msgs:
            if not self.event.original_args:
                return "Требуется аргументы или пересылаемые сообщения"

            msgs = [{'text': self.event.original_args, 'from_id': int(self.event.sender.user_id)}]
        issue_text = ""
        for msg in msgs:
            text = msg['text']
            if msg['from_id'] > 0:
                fwd_user_id = int(msg['from_id'])
                fwd_user = self.bot.get_user_by_id(fwd_user_id)
                username = fwd_user.name + " " + fwd_user.surname
            else:
                fwd_user_id = int(msg['from_id'])
                username = self.bot.get_bot_by_id(fwd_user_id).name
            issue_text += f"{username}:\n{text}\n\n"

        issue = IssueModel(
            author=self.event.sender,
            text=issue_text)
        issue.save()
        return "Сохранено"
