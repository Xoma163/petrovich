import json
from itertools import chain

import decimal


def db_instance2dict(instance):
    from django.db.models.fields.related import ManyToManyField
    metas = instance._meta
    data = {}
    for f in chain(metas.concrete_fields, metas.many_to_many):
        if isinstance(f, ManyToManyField):
            data[str(f.name)] = {tmp_object.pk: db_instance2dict(tmp_object)
                                 for tmp_object in f.value_from_object(instance)}
        elif f.is_relation:
            relation_instance = getattr(instance, f.name)
            if relation_instance:
                data[str(f.name)] = db_instance2dict(relation_instance)
            else:
                data[str(f.name)] = {'id': None}
        else:
            data[str(f.name)] = getattr(instance, f.name, False)
    return data


def serialize(instance):
    return json.dumps(db_instance2dict(instance), ensure_ascii=False, cls=DecimalEncoder)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)