from django.contrib.auth import get_user_model


Account = get_user_model()


class PasswordlessAuthentication(object):

    def authenticate(self, email=None, username=None, password=None, passwordless_key=None, force=False, **kwargs):

        # Django default admin login is looking for username
        if username:
            email = username
        user = None
        if email and password:
            user = Account.objects.filter(email__iexact=email).last()
            if user and not user.check_password(password):
                # Password didn't check out
                user = None
        elif passwordless_key:
            user = Account.objects.filter(passwordless_key=passwordless_key).last()

            if user and not user.is_passwordless and not force:
                # Cannot use a passwordless key for someone who has a password
                user = None
        return user

    def get_user(self, user_id):
        return Account.objects.filter(id=user_id).last()
