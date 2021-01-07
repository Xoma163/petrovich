# Метод вытаскивает все связанные сущности
import json
from itertools import chain


def db_instance2dict(instance):
    from django.db.models.fields.related import ManyToManyField
    metas = instance._meta
    data = {}
    for f in chain(metas.concrete_fields, metas.many_to_many):
        if isinstance(f, ManyToManyField):
            data[str(f.name)] = {tmp_object.pk: db_instance2dict(tmp_object)
                                 for tmp_object in f.value_from_object(instance)}
        else:
            data[str(f.name)] = str(getattr(instance, f.name, False))
    return data


def serialize(instance):
    return json.dumps(db_instance2dict(instance), ensure_ascii=False)
