from django.db import models
from django.db.models import JSONField
from django.utils.html import format_html

from apps.bot.api.gpt.usage import GPTAPIUsage
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
        ('gif', 'Гифка'),
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


class Donation(TimeStampModelMixin):
    username = models.CharField("Имя", max_length=100, blank=True, null=True)
    amount = models.CharField("Количество", max_length=10, blank=True)
    currency = models.CharField("Валюта", max_length=30, blank=True)
    message = models.CharField("Сообщение", max_length=1000, blank=True)
    date = models.DateTimeField("Дата", auto_now_add=True, blank=True)

    class Meta:
        verbose_name = "Донат"
        verbose_name_plural = "Донаты"
        ordering = ['-date']

    def __str__(self):
        username = self.username if self.username else "Аноним"
        return f"{username}. {self.amount}"


class Subscribe(TimeStampModelMixin):
    SERVICE_YOUTUBE = 1
    SERVICE_VK = 4
    SERVICE_CHOICES = (
        (SERVICE_YOUTUBE, 'YouTube'),
        (SERVICE_VK, 'VK'),
    )

    author = models.ForeignKey(User, models.CASCADE, verbose_name="Автор", null=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name='Чат', null=True, blank=True)
    message_thread_id = models.IntegerField("message_thread_id", blank=True, null=True, default=None)

    channel_id = models.CharField("ID канала", max_length=100, blank=True, null=True)
    playlist_id = models.CharField("ID плейлиста", max_length=100, blank=True, null=True)
    channel_title = models.CharField("Название канала", max_length=100)
    playlist_title = models.CharField("Название плейлиста", max_length=100, blank=True, null=True)
    last_videos_id = models.JSONField("ID последних видео", max_length=100, null=True, blank=True)  # array
    service = models.SmallIntegerField("Сервис", blank=True, choices=SERVICE_CHOICES, default=SERVICE_YOUTUBE)

    save_to_disk = models.BooleanField("Сохранять на диск", default=False)
    high_resolution = models.BooleanField("Присылать в высоком разрешении", default=False)
    force_cache = models.BooleanField("Принудительно кэшировать", default=False)

    @property
    def peer_id(self):
        return self.chat.chat_id if self.chat else self.author.user_id

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        if self.playlist_title:
            return f"{self.channel_title} | {self.playlist_title}"
        return self.channel_title


class VideoCache(TimeStampModelMixin):
    channel_id = models.CharField("ID канала", max_length=100)
    video_id = models.CharField("ID видео", max_length=100, null=True)
    filename = models.CharField('Название файла', max_length=1024)
    video = models.FileField('Видео', blank=True, upload_to="service/video/")

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


class Tag(TimeStampModelMixin):
    name = models.CharField("Название", max_length=100)
    users = models.ManyToManyField(Profile, verbose_name="Пользователи", blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        unique_together = ('name', 'chat')

    def __str__(self):
        return str(self.name)


class GPTPrePrompt(TimeStampModelMixin):
    CHATGPT = 'chatgpt'
    GEMINI = 'gemini'
    PROVIDER_CHOICES = (
        (CHATGPT, 'СhatGPT'),
        (GEMINI, 'Gemini')
    )

    author = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True, blank=True)
    chat = models.ForeignKey(Chat, models.CASCADE, verbose_name="Чат", null=True, blank=True)
    text = models.TextField("ChatGPT preprompt", default="", blank=True)
    provider = models.CharField('Провайдер', max_length=10, blank=True, choices=PROVIDER_CHOICES)

    class Meta:
        verbose_name = "GPT препромпт"
        verbose_name_plural = "GPT препромпты"
        unique_together = ('author', 'chat', 'provider')


class GPTUsage(TimeStampModelMixin):
    author = models.ForeignKey(Profile, models.CASCADE, verbose_name="Пользователь", null=True, db_index=True)
    cost = models.FloatField("Стоимость запроса", default=0)

    class Meta:
        verbose_name = "GPT использование"
        verbose_name_plural = "GPT использования"

    @classmethod
    def add_statistics(cls, sender: Profile, usage: GPTAPIUsage):
        GPTUsage(
            author=sender,
            cost=usage.total_cost
        ).save()
