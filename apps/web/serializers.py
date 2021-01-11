from rest_framework import serializers

from apps.web.models import CalculatorProduct, CalculatorUser, CalculatorSession


class CalculatorSessionMixin():
    def create(self, validated_data):
        instance = super().create(validated_data)
        if 'calculatorsession' in self.initial_data:
            session = CalculatorSession.objects.get(pk=self.initial_data['calculatorsession'])
            session.users.add(instance)
        return instance


class CalculatorUserSerializer(CalculatorSessionMixin, serializers.ModelSerializer):
    class Meta:
        model = CalculatorUser
        fields = "__all__"


class CalculatorProductSerializer(CalculatorSessionMixin, serializers.ModelSerializer, ):
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
