from django.contrib.postgres.fields import ArrayField
from django.db import models

from apps.bot.models import Profile, Chat
from apps.service.mixins import TimeStampModelMixin


class PetrovichUser(TimeStampModelMixin):
    profile = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)
    active = models.BooleanField("Активность", default=True)

    @property
    def wins(self):
        return PetrovichGame.objects.filter(profile=self.profile, chat=self.chat).count()

    def wins_by_year(self, year):
        return PetrovichGame.objects.filter(profile=self.profile, chat=self.chat, created_at__year=year).count()

    class Meta:
        verbose_name = "Петрович игрок"
        verbose_name_plural = "Петрович игроки"

    def __str__(self):
        return str(self.profile)


class PetrovichGame(TimeStampModelMixin):
    profile = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)

    class Meta:
        verbose_name = "Петровича игра"
        verbose_name_plural = "Петрович игры"

    def __str__(self):
        return str(self.profile)


class Wordle(TimeStampModelMixin):
    profile = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True)
    word = models.CharField(max_length=5)
    steps = models.PositiveIntegerField("Количество попыток", default=0)
    hypotheses = ArrayField(models.CharField(verbose_name="Гипотеза", max_length=5), verbose_name="Гипотезы",
                            max_length=6)
    message_id = models.IntegerField("id первого сообщения", blank=True, default=0)

    class Meta:
        verbose_name = 'Сессия "Wordle"'
        verbose_name_plural = 'Сессии "Wordle"'

    def __str__(self):
        return str(self.pk)
