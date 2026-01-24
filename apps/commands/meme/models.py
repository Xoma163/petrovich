from django.db import models

from apps.bot.models import Profile
from apps.shared.mixins import TimeStampModelMixin


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
    author = models.ForeignKey(Profile, models.SET_NULL, verbose_name="Профиль автора", null=True)
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
