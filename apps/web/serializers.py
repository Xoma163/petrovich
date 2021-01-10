import decimal
import json
# from itertools import chain

from rest_framework import serializers

from apps.web.models import CalculatorProduct, CalculatorUser, CalculatorSession

#
# def db_instance2dict(instance):
#     from django.db.models.fields.related import ManyToManyField
#     metas = instance._meta
#     data = {}
#     for f in chain(metas.concrete_fields, metas.many_to_many):
#         if isinstance(f, ManyToManyField):
#             data[str(f.name)] = {tmp_object.pk: db_instance2dict(tmp_object)
#                                  for tmp_object in f.value_from_object(instance)}
#         elif f.is_relation:
#             relation_instance = getattr(instance, f.name)
#             if relation_instance:
#                 data[str(f.name)] = db_instance2dict(relation_instance)
#             else:
#                 data[str(f.name)] = {'id': None}
#         else:
#             data[str(f.name)] = getattr(instance, f.name, False)
#     return data
#
#
# def serialize(instance):
#     return json.dumps(db_instance2dict(instance), ensure_ascii=False, cls=DecimalEncoder)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


class CalculatorUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculatorUser
        fields = "__all__"


class CalculatorProductSerializer(serializers.ModelSerializer):

    def save(self, **kwargs):
        instance = super().save(**kwargs)
        return instance

    def create(self, validated_data):
        instance = super().create(validated_data)
        if 'calculatorsession' in self.initial_data:
            session = CalculatorSession.objects.get(pk=self.initial_data['calculatorsession'])
            session.products.add(instance)
        return instance

    class Meta:
        model = CalculatorProduct
        fields = '__all__'


class CalculatorSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculatorSession
        fields = "__all__"


class CalculatorSessionViewSerializer(serializers.ModelSerializer):
    users = CalculatorUserSerializer(read_only=True, many=True)
    products = CalculatorProductSerializer(read_only=True, many=True)

    class Meta:
        model = CalculatorSession
        fields = "__all__"
