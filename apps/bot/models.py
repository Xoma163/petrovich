import random
from tempfile import NamedTemporaryFile

import requests
from django.contrib.auth.models import Group
from django.core.files import File
from django.db import models
from django.utils.html import format_html

from apps.bot.classes.consts.Consts import Platform as PlatformEnum


class Platform(models.Model):
    platform = models.CharField('Тип платформы', max_length=20, choices=PlatformEnum.choices())

    def get_platform_enum(self):
        return [x for x in PlatformEnum if x.name == self.platform][0]

    class Meta:
        abstract = True
        ordering = ["chat_id"]


class Chat(Platform):
    id = models.AutoField(primary_key=True)
    chat_id = models.CharField('ID чата', max_length=20, default="")
    name = models.CharField('Название', max_length=40, default="", blank=True)
    admin = models.ForeignKey('Users', models.SET_NULL, verbose_name='Админ', blank=True, null=True)

    need_reaction = models.BooleanField('Реагировать на неверные команды в конфе', default=True)
    mentioning = models.BooleanField('Работа без упоминания в конфе', default=False)
    need_meme = models.BooleanField('Слать мемы по точному названию', default=False)
    recognize_voice = models.BooleanField('Распозновать голосовые автоматически', default=True)
    is_banned = models.BooleanField('Забанен', default=False)

    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"

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
    user_id = models.CharField('ID пользователя', max_length=127)
    name = models.CharField('Имя', max_length=40, blank=True, null=True)
    surname = models.CharField('Фамилия', max_length=40, blank=True, null=True)
    nickname = models.CharField("Никнейм", max_length=40, blank=True, null=True)
    nickname_real = models.CharField("Прозвище", max_length=40, blank=True)
    gender = models.CharField('Пол', max_length=2, blank=True, choices=GENDER_CHOICES)
    birthday = models.DateField('Дата рождения', null=True, blank=True)
    # Здесь такой странный ForeignKey потому что проблема импортов
    city = models.ForeignKey('service.City', models.SET_NULL, verbose_name='Город', null=True, blank=True)

    groups = models.ManyToManyField(Group, verbose_name="Группы")

    chats = models.ManyToManyField(Chat, verbose_name="Чаты", blank=True, related_name="users")

    celebrate_bday = models.BooleanField('Поздравлять с Днём рождения', default=True)

    avatar = models.ImageField('Аватар', blank=True, upload_to="bot/users/avatar/")

    def set_avatar(self, url):
        ext = url.split('.')[-1].split('?')[0]
        image = NamedTemporaryFile()
        content = requests.get(url).content
        image.write(content)
        image.flush()

        self.avatar.save(f"avatar_{str(self)}.{ext}", File(image))

    def check_role(self, role):
        group = self.groups.filter(name=role.name)
        return group.exists()

    def get_list_of_role_names(self):
        groups = self.groups.all().values()
        return [group['name'] for group in groups]

    def show_url(self):
        if self.platform == PlatformEnum.VK.name:
            return format_html(f"<a href='https://vk.com/id{self.user_id}'>{self.platform}</a>")
        elif self.platform == PlatformEnum.TG.name:
            return format_html(f"<a href='https://t.me/{self.nickname}'>{self.platform}</a>")
        else:
            return self.platform

    show_url.short_description = "Ссылка"

    def show_user_id(self):
        if self.platform == PlatformEnum.VK.name or self.platform == PlatformEnum.TG.name:
            return self.user_id
        else:
            return self.user_id[:8] + "..."

    show_user_id.short_description = "user id"

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
    avatar = models.ImageField('Аватар', blank=True, upload_to="bot/bot/avatar/")

    class Meta:
        verbose_name = "Бот"
        verbose_name_plural = "Боты"
        ordering = ["id"]

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f"Неопознанный бот #{self.id}"

    def set_avatar(self, url):
        ext = url.split('.')[-1].split('?')[0]
        image = NamedTemporaryFile()
        content = requests.get(url).content
        image.write(content)
        image.flush()

        self.avatar.save(f"avatar_{str(self)}.{ext}", File(image))


def random_digits():
    digits_count = 6
    return str(random.randint(10 ** (digits_count - 1), 10 ** digits_count - 1))
