from rest_framework import serializers

from django.contrib.auth import get_user_model


Account = get_user_model()


class BasicAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id', )


class ExtendedAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ('id',  'email', )


class AccountSerializer(serializers.ModelSerializer):
    auth_token = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ('id', 'email', 'auth_token', 'first_name', 'last_name', )

    def get_auth_token(self, obj):
        return obj.auth_token.key
