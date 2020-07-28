from django.contrib.postgres.fields import JSONField
from django.db import models

from apps.bot.models import Users, Chat


class Gamer(models.Model):
    user = models.ForeignKey(Users, models.CASCADE, verbose_name="Игрок", null=True)
    points = models.IntegerField("Очки", default=0)
    tic_tac_toe_points = models.IntegerField("Очки крестики-нолики", default=0)
    codenames_points = models.IntegerField("Очки коднеймса", default=0)
    roulette_points = models.IntegerField("Очки рулетки", default=500)
    roulette_points_today = models.DateTimeField("Дата получения очков", auto_now_add=True)

    class Meta:
        verbose_name = "Игрок"
        verbose_name_plural = "Игроки"
        ordering = ["user"]

    def __str__(self):
        return str(self.user)


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
    user = models.ForeignKey(Users, models.CASCADE, verbose_name="Пользователь", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)
    wins = models.IntegerField("Побед в Петровиче", default=0)
    active = models.BooleanField("Активность", default=True)

    class Meta:
        verbose_name = "Петрович игрок"
        verbose_name_plural = "Петрович игроки"
        ordering = ["user"]

    def __str__(self):
        return str(self.user)


class PetrovichGames(models.Model):
    user = models.ForeignKey(Users, models.CASCADE, verbose_name="Пользователь", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)
    date = models.DateTimeField("Дата", auto_now_add=True, editable=True)

    class Meta:
        verbose_name = "Петровича игра"
        verbose_name_plural = "Петрович игры"
        ordering = ['-date']

    def __str__(self):
        return str(self.user)


def get_default_board():
    return [['', '', ''], ['', '', ''], ['', '', '']]


class TicTacToeSession(models.Model):
    user1 = models.ForeignKey(Users, models.CASCADE, "user1_%(class)ss", verbose_name="Пользователь *", null=True,
                              blank=True)
    user2 = models.ForeignKey(Users, models.CASCADE, "user2_%(class)ss", verbose_name="Пользователь o", null=True,
                              blank=True)
    next_step = models.ForeignKey(Users, models.CASCADE, "next_%(class)ss", verbose_name="Следующий шаг", null=True,
                                  blank=True)

    board = JSONField("Вложения", blank=True, default=get_default_board)

    class Meta:
        verbose_name = "Крестики-нолики сессия"
        verbose_name_plural = "Крестики-нолики сессии"
        ordering = ['-next_step']

    def __str__(self):
        return str(self.user1) + " " + str(self.user2)


class CodenamesUser(models.Model):
    user = models.ForeignKey(Users, models.CASCADE, verbose_name="Пользователь", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True)
    command_list = [('blue', "Синие"), ('red', "Красные")]
    command = models.CharField('Команда', choices=command_list, max_length=4, null=True, blank=True)
    role_list = [('captain', "Капитан"), ('player', "Игрок")]
    role = models.CharField('Роль', choices=role_list, default='player', max_length=7, null=True, blank=True)
    role_preference = models.CharField('Предпочтения(роль)', choices=role_list, default=None, max_length=7, null=True,
                                       blank=True)

    class Meta:
        verbose_name = "Коднеймс игрок"
        verbose_name_plural = "Коднеймс игроки"
        ordering = ["chat"]

    def __str__(self):
        return str(self.user)


class CodenamesSession(models.Model):
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True)
    # red, blue, red_wait, blue_wait, red_wait
    next_step_list = [('red', "Синие"), ('blue', "Красные"), ('blue_wait', "Капитан синих"),
                      ('red_wait', "Капитан красных")]
    next_step = models.CharField("Следующий шаг", null=True, blank=True, choices=next_step_list,
                                 default="blue_wait", max_length=10)
    count = models.IntegerField("Загадано слов", null=True, blank=True)
    word = models.CharField("Загаданное слово", null=True, blank=True, max_length=20)
    # [[{"Слово":"type"},{"Слово":"type"},...],...] type='red','blue','neutral','death'
    board = JSONField("Поле", blank=True, default=dict)

    class Meta:
        verbose_name = "Коднеймс сессия"
        verbose_name_plural = "Коднеймс сессии"
        ordering = ["chat"]

    def __str__(self):
        return str(self.id)


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
        return str(self.id)
