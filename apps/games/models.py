from django.db import models
from django.db.models import JSONField

from apps.bot.models import Profile, Chat


class Gamer(models.Model):
    profile = models.ForeignKey(Profile, models.CASCADE, verbose_name="Игрок", null=True)
    points = models.IntegerField("Очки ставок", default=0)
    roulette_points = models.IntegerField("Очки рулетки", default=500)
    roulette_points_today = models.DateTimeField("Дата получения очков", auto_now_add=True)

    class Meta:
        verbose_name = "Игрок"
        verbose_name_plural = "Игроки"
        ordering = ["profile"]

    def __str__(self):
        return str(self.profile)


class Rate(models.Model):
    gamer = models.ForeignKey(Gamer, models.CASCADE, verbose_name="Пользователь", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True)
    rate = models.IntegerField("Ставка")
    date = models.DateTimeField("Дата", auto_now_add=True, blank=True)
    random = models.BooleanField("Случайная", default=False)

    class Meta:
        verbose_name = "Ставка"
        verbose_name_plural = "Ставки"
        ordering = ["chat", "date"]

    def __str__(self):
        return str(self.chat) + " " + str(self.gamer)


class PetrovichUser(models.Model):
    profile = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)
    wins = models.IntegerField("Побед в Петровиче", default=0)
    active = models.BooleanField("Активность", default=True)

    class Meta:
        verbose_name = "Петрович игрок"
        verbose_name_plural = "Петрович игроки"
        ordering = ["profile"]

    def __str__(self):
        return str(self.profile)


class PetrovichGames(models.Model):
    profile = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)
    date = models.DateTimeField("Дата", auto_now_add=True, editable=True)

    class Meta:
        verbose_name = "Петровича игра"
        verbose_name_plural = "Петрович игры"
        ordering = ['-date']

    def __str__(self):
        return str(self.profile)


def get_default_board():
    return [['', '', ''], ['', '', ''], ['', '', '']]


class RouletteRate(models.Model):
    gamer = models.ForeignKey(Gamer, models.CASCADE, verbose_name="Игрок", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True)

    rate_on = JSONField("Ставка", blank=True, default=dict)
    rate = models.IntegerField("Размер ставки")

    class Meta:
        verbose_name = "Ставка рулеток"
        verbose_name_plural = "Ставки рулеток"
        ordering = ["chat"]

    def __str__(self):
        return str(self.pk)


class BullsAndCowsSession(models.Model):
    profile = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True)
    number = models.PositiveIntegerField("Загаданное число")
    steps = models.PositiveIntegerField("Количество попыток", default=1)

    class Meta:
        verbose_name = 'Сессия "Быки и коровы"'
        verbose_name_plural = 'Сессии "Быки и коровы"'
        ordering = ["chat"]

    def __str__(self):
        return str(self.pk)
