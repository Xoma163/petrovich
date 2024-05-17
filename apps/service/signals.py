import os

from django.db import models
from django.dispatch import receiver

from apps.service.models import VideoCache


@receiver(models.signals.post_delete, sender=VideoCache)
def auto_delete_file_on_delete(*args, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    instance = kwargs['instance']
    if instance.video and os.path.isfile(instance.video.path):
        os.remove(instance.video.path)
