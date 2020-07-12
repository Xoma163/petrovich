from apps.bot.classes.common.CommonCommand import CommonCommand
from apps.service.models import Counter as CounterModel


class Counter(CommonCommand):
    def __init__(self):
        names = ["счётчик", "счетчик", "счёт", "счет"]
        help_text = "Счётчик - счётчик события"
        detail_help_text = "Счётчик (событие) - счётчик события. Инкремент"
        super().__init__(names, help_text, detail_help_text, args=1)

    def start(self):
        name = self.event.original_args.capitalize()
        if len(name) >= 50:
            return "Длина названия счётчика не может превышать 50"
        counter, _ = CounterModel.objects.update_or_create(
            name=name, chat=self.event.chat,
            defaults={
                'name': name,
                'chat': self.event.chat
            })
        counter.count += 1
        counter.save()
        return "++"
