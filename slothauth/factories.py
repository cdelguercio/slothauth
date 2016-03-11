import factory

from django.contrib.auth import get_user_model
from django.utils import timezone


Account = get_user_model()


class AccountFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Account

    email = factory.Sequence(lambda n: 'email{0}@email.com'.format(n))
    is_staff = False
    is_active = True
    date_joined = timezone.now()
    passwordless_key = '12345'


class AdminFactory(AccountFactory):

    is_staff = True


class PasswordlessAccountFactory(AccountFactory):

    password = "!abcdefghijklmnopqrstuvwxyzabcdefghiklmn"
    passwordless_key = '12345'
