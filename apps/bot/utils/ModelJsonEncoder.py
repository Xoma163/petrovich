from enum import Enum

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model
from django.db.models.fields.files import ImageFieldFile


# from apps.bot.classes.Command import Command


class ModelJsonEncoder(DjangoJSONEncoder):

    def default(self, o):
        if isinstance(o, Model):
            # return model_to_dict(o)
            return str(o)
        if isinstance(o, ImageFieldFile):
            return str(o)
        if isinstance(o, Enum):
            return o.value
        try:
            return super().default(o)
        except Exception:
            return str(o)
