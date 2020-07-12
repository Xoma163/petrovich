from apps.bot.classes.Consts import Role
from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import Issue


class Issues(CommonCommand):
    def __init__(self):
        names = ["баги", "ишюс", "ишьюс", "иши"]
        help_text = "Баги - список проблем"
        super().__init__(names, help_text, access=Role.TRUSTED)

    def start(self):
        issues = Issue.objects.all()
        if not issues:
            return "Нет ишюсов!"
        features_text = "Добавленные ишю:\n\n"
        for i, feature in enumerate(issues):
            features_text += f"------------------------------{i + 1}------------------------------\n" \
                             f"{feature.text}\n"
        return features_text
