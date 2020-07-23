import random

from django.contrib.auth.models import Group
from django.db import models


# Create your models here.

class Platform(models.Model):
    PLATFORM_TG = 'tg'
    PLATFORM_VK = 'vk'
    PLATFORM_CHOICES = (
        (PLATFORM_TG, 'Telegram'),
        (PLATFORM_VK, 'Vk'))
    platform = models.CharField(verbose_name='Тип платформы', max_length=3, choices=PLATFORM_CHOICES)

    class Meta:
        abstract = True
        ordering = ["chat_id"]


class Chat(Platform):
    id = models.AutoField(primary_key=True)
    chat_id = models.CharField(verbose_name='ID чата', max_length=20, default="")
    name = models.CharField(verbose_name='Название', max_length=40, default="", blank=True)
    need_reaction = models.BooleanField(verbose_name='Реагировать', default=True)
    admin = models.ForeignKey('Users', verbose_name='Админ', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        ordering = ["chat_id"]

    def __str__(self):
        return str(self.name)


class Users(Platform):
    GENDER_FEMALE = '1'
    GENDER_MALE = '2'
    GENDER_NONE = ''
    GENDER_CHOICES = (
        (GENDER_FEMALE, 'женский'),
        (GENDER_MALE, 'мужской'),
        (GENDER_NONE, 'не указан'))

    id = models.AutoField(primary_key=True)
    user_id = models.CharField(verbose_name='ID пользователя', max_length=20)
    name = models.CharField(verbose_name='Имя', max_length=40, blank=True, null=True)
    surname = models.CharField(verbose_name='Фамилия', max_length=40, blank=True, null=True)
    nickname = models.CharField(verbose_name="Никнейм", max_length=40, blank=True, null=True)
    nickname_real = models.CharField(verbose_name="Прозвище", max_length=40, blank=True, default="")
    gender = models.CharField(verbose_name='Пол', max_length=2, blank=True, default="", choices=GENDER_CHOICES)
    birthday = models.DateField(verbose_name='Дата рождения', null=True, blank=True)
    # Здесь такой странный ForeignKey потому что проблема импортов
    city = models.ForeignKey('service.City', verbose_name='Город', null=True, blank=True, on_delete=models.SET_NULL)

    groups = models.ManyToManyField(Group, verbose_name="Группы")

    chats = models.ManyToManyField(Chat, verbose_name="Чаты", blank=True)

    imei = models.CharField('IMEI', max_length=20, null=True, blank=True)
    send_notify_to = models.ManyToManyField('self', verbose_name="Отправлять уведомления", blank=True)

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["name", "surname"]

    def __str__(self):
        if self.name and self.surname:
            return f"{self.name} {self.surname}"
        elif self.name:
            return str(self.name)
        else:
            return "Незарегистрированный пользователь"


class Bot(Platform):
    id = models.AutoField(primary_key=True)
    bot_id = models.CharField(verbose_name='ID бота', max_length=20)
    name = models.CharField(verbose_name='Имя', max_length=40)

    class Meta:
        verbose_name = "Бот"
        verbose_name_plural = "Боты"
        ordering = ["id"]

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f"Неопознанный бот #{self.id}"


class APIUser(models.Model):
    user = models.ForeignKey(Users, verbose_name="Юзер", on_delete=models.CASCADE, null=True, blank=True)
    chat = models.ForeignKey(Chat, verbose_name="Вк чат", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = "API Пользователь"
        verbose_name_plural = "API Пользователи"

    def __str__(self):
        return str(self.user)


def random_digits():
    digits_count = 6
    return str(random.randint(10 ** (digits_count - 1), 10 ** digits_count - 1))


class APITempUser(models.Model):
    user = models.ForeignKey(Users, verbose_name="Пользователь", on_delete=models.CASCADE, null=True, blank=True)
    chat = models.ForeignKey(Chat, verbose_name="Чат", on_delete=models.CASCADE, null=True, blank=True)
    code = models.CharField(verbose_name="Код подтверждения", default=random_digits, max_length=6)
    tries = models.IntegerField(verbose_name="Кол-во попыток", default=5)

    class Meta:
        verbose_name = "API Временный пользователь"
        verbose_name_plural = "API Временные пользователи"

    def __str__(self):
        return str(self.user)
