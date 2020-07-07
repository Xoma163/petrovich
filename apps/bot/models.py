import random

from django.contrib.auth.models import Group
from django.db import models


# Create your models here.

class AbstractChat(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    chat_id = models.CharField(verbose_name='ID чата', max_length=20, default="")
    name = models.CharField(verbose_name='Название', max_length=40, default="", blank=True)
    need_reaction = models.BooleanField(verbose_name='Реагировать', default=True)

    class Meta:
        abstract = True
        ordering = ["chat_id"]

    def __str__(self):
        return str(self.name)


class AbstractUser(models.Model):
    GENDER_FEMALE = '1'
    GENDER_MALE = '2'
    GENDER_NONE = ''
    GENDER_CHOICES = (
        (GENDER_FEMALE, 'женский'),
        (GENDER_MALE, 'мужской'),
        (GENDER_NONE, 'не указан'))

    id = models.AutoField(primary_key=True, verbose_name='ID')

    user_id = models.CharField(verbose_name='ID пользователя', max_length=20)
    name = models.CharField(verbose_name='Имя', max_length=40, default="")
    surname = models.CharField(verbose_name='Фамилия', max_length=40, default="")
    nickname = models.CharField(verbose_name="Никнейм", max_length=40, blank=True, default="")
    nickname_real = models.CharField(verbose_name="Прозвище", max_length=40, blank=True, default="")
    gender = models.CharField(verbose_name='Пол', max_length=2, blank=True, default="", choices=GENDER_CHOICES)
    birthday = models.DateField(verbose_name='Дата рождения', null=True, blank=True)
    # Здесь такой странный ForeignKey потому что проблема импортов
    city = models.ForeignKey('service.City', verbose_name='Город', null=True, blank=True, on_delete=models.SET_NULL)

    # imei = models.CharField(verbose_name='IMEI', max_length=20, null=True, blank=True)

    groups = models.ManyToManyField(Group, verbose_name="Группы")

    # send_notify_to = models.ManyToManyField('self', verbose_name="Отправление уведомлений", blank=True)

    class Meta:
        abstract = True
        ordering = ["name", "surname"]

    def __str__(self):
        return f"{self.name} {self.surname}"


class AbstractBot(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    bot_id = models.CharField(verbose_name='ID бота', max_length=20)
    name = models.CharField(verbose_name='Имя', max_length=40, default="")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class VkChat(AbstractChat):
    admin = models.ForeignKey('VkUser', verbose_name='Админ', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "ВК Чат"
        verbose_name_plural = "ВК Чаты"


class VkUser(AbstractUser):
    chats = models.ManyToManyField(VkChat, verbose_name="Чаты", blank=True)

    class Meta:
        verbose_name = "ВК Пользователь"
        verbose_name_plural = "ВК Пользователи"


class VkBot(AbstractBot):
    class Meta:
        verbose_name = "ВК Бот"
        verbose_name_plural = "ВК Боты"


class TgChat(AbstractChat):
    admin = models.ForeignKey('TgUser', verbose_name='Админ', blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = "ТГ Чат"
        verbose_name_plural = "ТГ Чаты"


class TgUser(AbstractUser):
    chats = models.ManyToManyField(TgChat, verbose_name="Чаты", blank=True)

    class Meta:
        verbose_name = "ТГ Пользователь"
        verbose_name_plural = "ТГ Пользователи"


class TgBot(AbstractBot):
    class Meta:
        verbose_name = "ТГ Бот"
        verbose_name_plural = "ТГ Боты"


class APIUser(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    user_id = models.CharField(verbose_name="ID пользователя", max_length=100)
    vk_user = models.ForeignKey(VkUser, verbose_name="Вк юзер", on_delete=models.CASCADE, null=True, blank=True)
    vk_chat = models.ForeignKey(VkChat, verbose_name="Вк чат", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        verbose_name = "API Пользователь"
        verbose_name_plural = "API Пользователи"

    def __str__(self):
        return str(self.vk_user)


def random_digits():
    digits_count = 6
    return str(random.randint(10 ** (digits_count - 1), 10 ** digits_count - 1))


class APITempUser(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    user_id = models.CharField(verbose_name="ID пользователя", max_length=100)
    vk_user = models.ForeignKey(VkUser, verbose_name="Вк юзер", on_delete=models.CASCADE, null=True, blank=True)
    vk_chat = models.ForeignKey(VkChat, verbose_name="Вк чат", on_delete=models.CASCADE, null=True, blank=True)
    code = models.CharField(verbose_name="Код подтверждения", default=random_digits, max_length=6)
    tries = models.IntegerField(verbose_name="Кол-во попыток", default=5)

    class Meta:
        verbose_name = "API Временный пользователь"
        verbose_name_plural = "API Временные пользователи"

    def __str__(self):
        return str(self.vk_user)
