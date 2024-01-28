from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import JSONField

from apps.bot.models import Profile, Chat


class Gamer(models.Model):
    points = models.IntegerField("Очки ставок", default=0)
    roulette_points = models.IntegerField("Очки рулетки", default=500)
    bk_points = models.IntegerField("Очки быки и коровы", default=0)
    wordle_points = models.IntegerField("Очки Wordle", default=0)
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
    active = models.BooleanField("Активность", default=True)

    @property
    def wins(self):
        return PetrovichGames.objects.filter(profile=self.profile, chat=self.chat).count()

    def wins_by_year(self, year):
        return PetrovichGames.objects.filter(profile=self.profile, chat=self.chat, date__year=year).count()

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
    message_id = models.IntegerField("id первого сообщения", blank=True, default=0)
    message_body = models.TextField("Тело сообщения для игры в одном сообщении", blank=True)

    class Meta:
        verbose_name = 'Сессия "Быки и коровы"'
        verbose_name_plural = 'Сессии "Быки и коровы"'
        ordering = ["chat"]

    def __str__(self):
        return str(self.pk)


class Wordle(models.Model):
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
        ordering = ["chat"]

    def __str__(self):
        return str(self.pk)
