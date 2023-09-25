import os

from django.db import models
from django.db.models import JSONField
from django.dispatch import receiver
from django.utils.html import format_html

from apps.bot.models import Chat, Profile, User


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


class BaseMeme(models.Model):
    ATTACHMENT_NAMES = [
        ('photo', 'Фото'),
        ('video', 'Видео'),
        ('link', 'Ссылка'),
        ('sticker', 'Стикер'),
        ('gif', 'Гифка'),
        ('voice', 'Голосовое'),
        ('video_note', 'Кружочек'),
    ]
    name = models.CharField("Название", max_length=1000, default="")
    link = models.CharField("Ссылка", max_length=1000, default="", null=True, blank=True)
    author = models.ForeignKey(Profile, models.SET_NULL, verbose_name="Автор", null=True)
    type = models.CharField("Тип", max_length=10, choices=ATTACHMENT_NAMES, blank=True)
    uses = models.PositiveIntegerField("Использований", default=0)
    approved = models.BooleanField("Разрешённый", default=False)

    tg_file_id = models.CharField("file_id в tg", max_length=128, blank=True)

    def get_info(self):
        info = f"Название: {self.name}\n" \
               f"Тип: {self.get_type_display()}\n" \
               f"ID: {self.pk}\n" \
               f"Автор: {self.author}\n" \
               f"Использований: {self.uses}"
        if self.link:
            info += f"\nСсылка: {self.link}"
        return info

    def preview_image(self):
        if self.link and self.type == 'photo':
            return format_html('<img src="{src}" width="150"/>', src=self.link)
        else:
            return '(Нет изображения)'

    def preview_link(self):
        if self.link:
            return format_html('<a href="{href}">Тык</a>', href=self.link)
        else:
            return '(Нет изображения)'

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.name)


class Meme(BaseMeme):
    class Meta:
        verbose_name = "мем"
        verbose_name_plural = "мемы"
        ordering = ["name"]


class Notify(models.Model):
    date = models.DateTimeField("Дата напоминания", null=True, blank=True)
    crontab = models.CharField("Crontab", max_length=100, null=True, blank=True)
    text = models.CharField("Текст/команда", max_length=1000, default="", blank=True)
    text_for_filter = models.CharField("Текст для поиска", max_length=1000, default="")
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)
    user = models.ForeignKey(User, models.CASCADE, verbose_name="Пользователь", null=True, blank=True)
    repeat = models.BooleanField("Повторять", default=False)
    mention_sender = models.BooleanField("Упоминать автора", default=True)
    attachments = JSONField("Вложения", blank=True, default=dict)
    message_thread_id = models.IntegerField("message_thread_id", blank=True, null=True, default=None)

    class Meta:
        verbose_name = "напоминание"
        verbose_name_plural = "напоминания"
        ordering = ["user"]

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


class Subscribe(models.Model):
    SERVICE_YOUTUBE = 1
    SERVICE_THE_HOLE = 2
    SERVICE_VK = 4
    SERVICE_PREMIERE = 5
    SERVICE_CHOICES = (
        (SERVICE_YOUTUBE, 'YouTube'),
        (SERVICE_THE_HOLE, 'The Hole'),
        (SERVICE_VK, 'VK'),
        (SERVICE_PREMIERE, 'Premiere'),
    )

    author = models.ForeignKey(User, models.CASCADE, verbose_name="Автор", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)

    channel_id = models.CharField("ID канала", max_length=100)
    playlist_id = models.CharField("ID плейлиста", max_length=100, blank=True, null=True)
    title = models.CharField("Название канала", max_length=100)
    date = models.DateTimeField("Дата последней публикации", null=True, blank=True)
    last_video_id = models.CharField("ID последнего видео", max_length=100, null=True, blank=True)

    service = models.SmallIntegerField("Сервис", blank=True, choices=SERVICE_CHOICES, default=SERVICE_YOUTUBE)

    is_stream = models.BooleanField("Флаг стрима", blank=True, default=False)
    last_stream_status = models.BooleanField("Последнее состояние стрима", blank=True,
                                             default=False)  # True - активен, False - нет

    message_thread_id = models.IntegerField("message_thread_id", blank=True, null=True, default=None)

    save_to_plex = models.BooleanField("Сохранять в plex", default=False)

    @property
    def peer_id(self):
        return self.chat.chat_id if self.chat else self.author.user_id

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ['title']

    def __str__(self):
        return self.title


class VideoCache(models.Model):
    channel_id = models.CharField("ID канала", max_length=100)
    video_id = models.CharField("ID видео", max_length=100, null=True)
    filename = models.CharField('Название файла', max_length=256)
    video = models.FileField('Видео', blank=True, upload_to="service/video/")

    class Meta:
        unique_together = ('channel_id', 'video_id')
        verbose_name = "Кэш видео"
        verbose_name_plural = "Кэши видео"
        ordering = ['filename']

    def __str__(self):
        return self.filename


@receiver(models.signals.post_delete, sender=VideoCache)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.video:
        if os.path.isfile(instance.video.path):
            os.remove(instance.video.path)


class HoroscopeMeme(BaseMeme):
    meme_pk = models.PositiveIntegerField(verbose_name="ID мема", blank=True, default=0)

    def get_info(self):
        info = f"Название: {self.name}\n" \
               f"Тип: {self.get_type_display()}\n" \
               f"ID: {self.meme_pk}\n" \
               f"Автор: {self.author}\n" \
               f"Использований: {self.uses}"
        if self.link:
            info += f"\nСсылка: {self.link}"
        return info

    class Meta:
        verbose_name = "мем гороскопа"
        verbose_name_plural = "мемы гороскопа"
        ordering = ["name"]


class Horoscope(models.Model):
    memes = models.ManyToManyField(HoroscopeMeme)

    class Meta:
        verbose_name = "Гороскоп"
        verbose_name_plural = "Гороскопы"

    def __str__(self):
        return str(self.pk)


class WakeOnLanUserData(models.Model):
    author = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True)
    name = models.CharField("Название", max_length=100)
    ip = models.CharField("IP", max_length=16)
    port = models.SmallIntegerField("Порт")
    mac = models.CharField("MAC адрес", max_length=17)

    class Meta:
        verbose_name = "WOL устройство"
        verbose_name_plural = "WOL устройства"

    def __str__(self):
        return f"{self.author}-{self.name} {self.ip}:{self.port}"


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

    class Meta:
        verbose_name = "Инфо о такси"
        verbose_name_plural = "Инфо о такси"


class Tag(models.Model):
    name = models.CharField("Название", max_length=100)
    users = models.ManyToManyField(Profile, verbose_name="Пользователи", blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']
        unique_together = ('name', 'chat')

    def __str__(self):
        return str(self.name)
