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
    platform = models.CharField('Тип платформы', max_length=3, choices=PLATFORM_CHOICES)

    class Meta:
        abstract = True
        ordering = ["chat_id"]


class Chat(Platform):
    id = models.AutoField(primary_key=True)
    chat_id = models.CharField('ID чата', max_length=20, default="")
    name = models.CharField('Название', max_length=40, default="", blank=True)
    need_reaction = models.BooleanField('Реагировать', default=True)
    admin = models.ForeignKey('Users', models.SET_NULL, verbose_name='Админ', blank=True, null=True)

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
    user_id = models.CharField('ID пользователя', max_length=20)
    name = models.CharField('Имя', max_length=40, blank=True, null=True)
    surname = models.CharField('Фамилия', max_length=40, blank=True, null=True)
    nickname = models.CharField("Никнейм", max_length=40, blank=True, null=True)
    nickname_real = models.CharField("Прозвище", max_length=40, blank=True)
    gender = models.CharField('Пол', max_length=2, blank=True, choices=GENDER_CHOICES)
    birthday = models.DateField('Дата рождения', null=True, blank=True)
    # Здесь такой странный ForeignKey потому что проблема импортов
    city = models.ForeignKey('service.City', models.SET_NULL, verbose_name='Город', null=True, blank=True)

    groups = models.ManyToManyField(Group, verbose_name="Группы")

    chats = models.ManyToManyField(Chat, verbose_name="Чаты", blank=True)

    imei = models.CharField('IMEI', max_length=20, null=True, blank=True)
    send_notify_to = models.ManyToManyField('self', verbose_name="Отправлять уведомления", blank=True)

    def check_role(self, role):
        group = self.groups.filter(name=role.name)
        return group.exists()

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
    bot_id = models.CharField('ID бота', max_length=20)
    name = models.CharField('Имя', max_length=40)

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
    user = models.ForeignKey(Users, models.CASCADE, verbose_name="Юзер", null=True, blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Вк чат", null=True, blank=True)

    class Meta:
        verbose_name = "API Пользователь"
        verbose_name_plural = "API Пользователи"

    def __str__(self):
        return str(self.user)


def random_digits():
    digits_count = 6
    return str(random.randint(10 ** (digits_count - 1), 10 ** digits_count - 1))


class APITempUser(models.Model):
    user = models.ForeignKey(Users, models.CASCADE, verbose_name="Пользователь", null=True, blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True, blank=True)
    code = models.CharField("Код подтверждения", default=random_digits, max_length=6)
    tries = models.IntegerField("Кол-во попыток", default=5)

    class Meta:
        verbose_name = "API Временный пользователь"
        verbose_name_plural = "API Временные пользователи"

    def __str__(self):
        return str(self.user)
