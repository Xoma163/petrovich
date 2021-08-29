import os
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from django.core.files import File
from django.db import models
from django.db.models import JSONField
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from apps.bot.models import Chat, Users, Bot
from petrovich.settings import MEDIA_ROOT


class TimeZone(models.Model):
    name = models.CharField("Временная зона UTC", null=True, max_length=30)

    class Meta:
        verbose_name = "таймзона"
        verbose_name_plural = "таймзоны"
        ordering = ["name"]

    def __str__(self):
        return str(self.name)


class City(models.Model):
    name = models.CharField("Название", max_length=100)
    synonyms = models.CharField("Похожие названия", max_length=300)
    timezone = models.ForeignKey(TimeZone, models.SET_NULL, verbose_name="Временная зона UTC", null=True, default="")
    lat = models.FloatField("Широта", null=True)
    lon = models.FloatField("Долгота", null=True)

    class Meta:
        verbose_name = "город"
        verbose_name_plural = "города"
        ordering = ["name"]

    def __str__(self):
        return str(self.name)


class Service(models.Model):
    name = models.CharField(primary_key=True, verbose_name="Имя", max_length=50)
    value = models.CharField("Значение", max_length=5000, default="", null=True)
    update_datetime = models.DateTimeField("Дата создания", auto_now=True)

    class Meta:
        verbose_name = "сервис"
        verbose_name_plural = "сервисы"

    def __str__(self):
        return self.name


class Counter(models.Model):
    name = models.CharField("Имя", max_length=50, blank=True)
    count = models.IntegerField("Количество", default=0)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)

    class Meta:
        verbose_name = "счётчик"
        verbose_name_plural = "счётчики"

    def __str__(self):
        return self.name


def get_image_from_url(url):
    if url:
        ext = url.split('.')[-1].split('?')[0]
        img_temp = NamedTemporaryFile()
        img_temp.write(urlopen(url).read())
        img_temp.flush()
        return ext, img_temp


class Cat(models.Model):
    image = models.ImageField("Изображение", upload_to='service/cats/')
    author = models.ForeignKey(Users, models.SET_NULL, verbose_name="Автор", null=True)
    to_send = models.BooleanField("Ещё не было", default=True)

    class Meta:
        verbose_name = "кот"
        verbose_name_plural = "коты"

    def __str__(self):
        return str(self.id)

    def save_remote_image(self, url):
        if not self.image:
            ext, image = get_image_from_url(url)
            self.image.save(f"cat.{ext}", File(image))
        self.save()

    def preview(self):
        if self.image:
            from django.utils.safestring import mark_safe
            return mark_safe(u'<img src="{0}" width="150"/>'.format(self.image.url))
        else:
            return '(Нет изображения)'


class Meme(models.Model):
    types = [
        ('photo', 'Фото'),
        ('video', 'Видео'),
        ('audio', 'Аудио'),
        ('doc', 'Документ'),
        ('link', 'Ссылка'),
    ]

    name = models.CharField("Название", max_length=1000, default="")
    link = models.CharField("Ссылка", max_length=1000, default="", null=True, blank=True)
    author = models.ForeignKey(Users, models.SET_NULL, verbose_name="Автор", null=True)
    type = models.CharField("Тип", max_length=5, choices=types, blank=True)
    uses = models.PositiveIntegerField("Использований", default=0)
    approved = models.BooleanField("Разрешённый", default=False)

    def get_info(self):
        return f"Название: {self.name}\n" \
               f"Тип: {self.get_type_display()}\n" \
               f"ID: {self.pk}\n" \
               f"Автор: {self.author}\n" \
               f"Ссылка: {self.link}\n" \
               f"Использований: {self.uses}\n"

    class Meta:
        verbose_name = "мем"
        verbose_name_plural = "мемы"
        ordering = ["name"]

    def __str__(self):
        return str(self.name)

    def preview_image(self):
        if self.link:
            from django.utils.safestring import mark_safe
            return mark_safe(u'<img src="{0}" width="150"/>'.format(self.link))
        else:
            return '(Нет изображения)'

    def preview_link(self):
        if self.link:
            from django.utils.safestring import mark_safe
            cropped_link = self.link
            if len(cropped_link) > 100:
                cropped_link = f"{self.link[:98]}..."
            return mark_safe(u'<a href="{0}">Тык</a>'.format(self.link, cropped_link))
        else:
            return '(Нет изображения)'


@receiver(pre_delete, sender=Cat, dispatch_uid='question_delete_signal')
def log_deleted_question(sender, instance, using, **kwargs):
    if instance.image:
        delete_path = f'{MEDIA_ROOT}/{instance.image}'
        try:
            os.remove(delete_path)
        except FileNotFoundError:
            print("Warn: Кот удалён, но файл картинки не найден")


class Notify(models.Model):
    date = models.DateTimeField("Дата напоминания")
    text = models.CharField("Текст/команда", max_length=1000, default="")
    text_for_filter = models.CharField("Текст для поиска", max_length=1000, default="")
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)
    author = models.ForeignKey(Users, models.CASCADE, verbose_name="Автор", null=True)
    repeat = models.BooleanField("Повторять", default=False)
    attachments = JSONField("Вложения", blank=True, default=dict)

    class Meta:
        verbose_name = "напоминание"
        verbose_name_plural = "напоминания"
        ordering = ["date"]

    def __str__(self):
        return str(self.text)


class Donations(models.Model):
    username = models.CharField("Имя", max_length=100, blank=True)
    amount = models.CharField("Количество", max_length=10, blank=True)
    currency = models.CharField("Валюта", max_length=30, blank=True)
    message = models.CharField("Сообщение", max_length=1000, blank=True)
    date = models.DateTimeField("Дата", auto_now_add=True, blank=True)

    class Meta:
        verbose_name = "Донат"
        verbose_name_plural = "Донаты"
        ordering = ['-date']

    def __str__(self):
        return f"{self.username}. {self.amount}"


class YoutubeSubscribe(models.Model):
    author = models.ForeignKey(Users, models.CASCADE, verbose_name="Автор", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)

    channel_id = models.CharField("ID канала", max_length=100)
    title = models.CharField("Название канала", max_length=100)
    date = models.DateTimeField("Дата последней публикации")

    class Meta:
        verbose_name = "Подписка ютуба"
        verbose_name_plural = "Подписки ютуба"
        ordering = ['title']

    def __str__(self):
        return self.title


class Horoscope(models.Model):
    memes = models.ManyToManyField(Meme)

    class Meta:
        verbose_name = "Гороскоп"
        verbose_name_plural = "Гороскопы"

    def __str__(self):
        return str(self.pk)


class WakeOnLanUserData(models.Model):
    user = models.ForeignKey(Users, models.CASCADE, verbose_name="Пользователь", null=True)
    name = models.CharField("Название", max_length=100)
    ip = models.CharField("IP", max_length=16)
    port = models.SmallIntegerField("Порт")
    mac = models.CharField("MAC адрес", max_length=17)

    class Meta:
        verbose_name = "WOL устройство"
        verbose_name_plural = "WOL устройства"

    def __str__(self):
        return f"{self.user}-{self.name} {self.ip}:{self.port}"


class QuoteBook(models.Model):
    text = models.TextField("Текст", max_length=5000)
    date = models.DateTimeField("Дата", auto_now_add=True, blank=True)
    user = models.ForeignKey(Users, models.CASCADE, verbose_name="Автор", null=True, blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True, blank=True)

    class Meta:
        verbose_name = "Цитата"
        verbose_name_plural = "Цитаты"
        ordering = ['-date']

    def __str__(self):
        return str(self.text)


class Words(models.Model):
    m1 = models.CharField("Мужской", max_length=500, null=True)
    f1 = models.CharField("Женский", max_length=500, null=True)
    n1 = models.CharField("Средний", max_length=500, null=True)
    mm = models.CharField("Множественный мужской", max_length=500, null=True)
    fm = models.CharField("Множественный женский", max_length=500, null=True)

    type = models.CharField('Тип', choices=(('bad', 'Плохое'), ('good', 'Хорошее')), default="bad",
                            max_length=10)

    class Meta:
        verbose_name = "Слово"
        verbose_name_plural = "Слова"
        ordering = ['type', 'id']

    def __str__(self):
        return str(self.m1)


class TaxiInfo(models.Model):
    data = JSONField("Данные", default=dict)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.created)
