from django.db import models
from django.db.models import JSONField

from apps.bot.models import Chat, Profile, User
from apps.service.mixins import TimeStampModelMixin


class TimeZone(models.Model):
    name = models.CharField("Временная зона UTC", null=True, max_length=30)

    class Meta:
        verbose_name = "таймзона"
        verbose_name_plural = "таймзоны"

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

    def __str__(self):
        return str(self.name)


class Service(TimeStampModelMixin):
    name = models.CharField(primary_key=True, verbose_name="Имя", max_length=50)
    value = models.CharField("Значение", max_length=5000, default="", null=True)
    update_datetime = models.DateTimeField("Дата создания", auto_now=True)

    class Meta:
        verbose_name = "сервис"
        verbose_name_plural = "сервисы"

    def __str__(self):
        return self.name


class BaseMeme(TimeStampModelMixin):
    ATTACHMENT_NAMES = [
        ('photo', 'Фото'),
        ('video', 'Видео'),
        ('link', 'Ссылка'),
        ('sticker', 'Стикер'),
        # ToDo: в чём разница между gif и animation. Animation - свежее как будто?
        ('gif', 'Гифка'),
        ('animation', 'Гифка'),
        ('voice', 'Голосовое'),
        ('video_note', 'Кружочек'),
    ]
    name = models.CharField("Название", max_length=1000, default="")
    link = models.CharField("Ссылка", max_length=1000, default="", null=True, blank=True)
    author = models.ForeignKey(Profile, models.SET_NULL, verbose_name="Автор", null=True)
    type = models.CharField("Тип", max_length=10, choices=ATTACHMENT_NAMES, blank=True)
    uses = models.PositiveIntegerField("Использований", default=0)
    inline_uses = models.PositiveIntegerField("Рекомендаций в inline", default=0)
    approved = models.BooleanField("Разрешённый", default=False)
    for_trusted = models.BooleanField("Для доверенных пользователей", default=False)
    file = models.FileField("Файл", upload_to="service/memes", null=True)
    file_preview = models.FileField("Файл превью", upload_to="service/memes_preview", null=True)

    tg_file_id = models.CharField("file_id в tg", max_length=128, blank=True)

    def get_info(self):
        info = f"Название: {self.name}\n" \
               f"ID: {self.pk}\n" \
               f"Автор: {self.author}\n" \
               f"Использований: {self.uses}\n" \
               f"Использований в inline: {self.inline_uses}"
        if self.link:
            info += f"\nСсылка: {self.link}"
        if self.for_trusted:
            info += "\nДля доверенных: Да"
        return info

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.name)


class Meme(BaseMeme):
    class Meta:
        verbose_name = "мем"
        verbose_name_plural = "мемы"


class Notify(TimeStampModelMixin):
    date = models.DateTimeField("Дата напоминания", null=True, blank=True)
    crontab = models.CharField("Crontab", max_length=100, null=True, blank=True)
    text = models.CharField("Текст/команда", max_length=1000, default="", blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)
    user = models.ForeignKey(User, models.CASCADE, verbose_name="Пользователь", null=True, blank=True)
    mention_sender = models.BooleanField("Упоминать автора", default=True)
    attachments = JSONField("Вложения", blank=True, default=dict)
    message_thread_id = models.IntegerField("message_thread_id", blank=True, null=True, default=None)

    class Meta:
        verbose_name = "напоминание"
        verbose_name_plural = "напоминания"

    def __str__(self):
        return str(self.text)


class VideoCache(TimeStampModelMixin):
    channel_id = models.CharField("ID канала", max_length=100)
    video_id = models.CharField("ID видео", max_length=100, null=True)
    filename = models.CharField('Название файла', max_length=1024)
    video = models.FileField('Видео', blank=True, upload_to="service/video/", max_length=1024)
    original_url = models.URLField("Ссылка на оригинальное видео", blank=True, max_length=1024)

    class Meta:
        unique_together = ('channel_id', 'video_id')
        verbose_name = "Кэш видео"
        verbose_name_plural = "Кэши видео"

    def __str__(self):
        return self.filename


class HoroscopeMeme(BaseMeme):
    meme_pk = models.PositiveIntegerField(verbose_name="ID мема", blank=True, default=0)

    class Meta:
        verbose_name = "мем гороскопа"
        verbose_name_plural = "мемы гороскопа"

    def get_info(self):
        info = f"Название: {self.name}\n" \
               f"ID: {self.meme_pk}\n" \
               f"Автор: {self.author}\n" \
               f"Использований: {self.uses}\n" \
               f"Использований в inline: {self.inline_uses}"
        if self.link:
            info += f"\nСсылка: {self.link}"
        return info


class Horoscope(models.Model):
    memes = models.ManyToManyField(HoroscopeMeme)
    date = models.DateField("Дата", null=True)

    class Meta:
        verbose_name = "Гороскоп"
        verbose_name_plural = "Гороскопы"

    def __str__(self):
        return str(self.pk)


