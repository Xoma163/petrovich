import os

from django.db import models
from django.dispatch import receiver

from apps.commands.media_command.models import VideoCache


@receiver(models.signals.post_delete, sender=VideoCache)
def delete_file_with_record(instance, **kwargs):  # noqa
    """
    Deletes file from filesystem
    when corresponding `MediaFile` object is deleted.
    """
    if instance.video and os.path.isfile(instance.video.path):
        os.remove(instance.video.path)
