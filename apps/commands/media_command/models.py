from django.db import models

from apps.shared.mixins import TimeStampModelMixin


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
