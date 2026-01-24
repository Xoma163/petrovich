from django.db import models
from django.db.models import JSONField

from apps.bot.models import Chat, User
from apps.shared.mixins import TimeStampModelMixin


# Create your models here.
class Notify(TimeStampModelMixin):
    date = models.DateTimeField("Дата напоминания", null=True, blank=True)
    crontab = models.CharField("Crontab", max_length=100, null=True, blank=True)
    text = models.CharField("Текст/команда", max_length=1000, default="", blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True,
                             related_name='+')  # TODO: +
    user = models.ForeignKey(User, models.CASCADE, verbose_name="Пользователь", null=True, blank=True,
                             related_name='+')  # TODO +
    mention_sender = models.BooleanField("Упоминать автора", default=True)
    attachments = JSONField("Вложения", blank=True, default=dict)
    message_thread_id = models.IntegerField("message_thread_id", blank=True, null=True, default=None)

    class Meta:
        verbose_name = "напоминание"
        verbose_name_plural = "напоминания"

    def __str__(self):
        return str(self.text)
