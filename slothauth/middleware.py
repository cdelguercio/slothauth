from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model

from . import settings


Account = get_user_model()


class PasswordlessUserMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        passwordless_key = request.GET.get(settings.PASSWORDLESS_GET_PARAM, None)
        if passwordless_key and not (passwordless_key == ''):
            user = authenticate(passwordless_key=passwordless_key,
                                force=True)  # TODO adding force makes the passwordless key authenticate users WITH a password too via passwordless key
            if user and user.is_active:
                login(request, user)

        response = self.get_response(request)

        return response


class OneTimeAuthenticationKeyMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        one_time_authentication_key = request.GET.get(settings.ONE_TIME_AUTHENTICATION_KEY_GET_PARAM, None)
        if one_time_authentication_key and not (one_time_authentication_key == ''):
            user = authenticate(one_time_authentication_key=one_time_authentication_key)
            if user and user.is_active:
                login(request, user)

        response = self.get_response(request)

        return response


class ImpersonateMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        impersonating = None
        if hasattr(request.user, 'can_impersonate') and request.user.can_impersonate and "__impersonate" in request.GET:
            request.session['impersonate_id'] = int(request.GET["__impersonate"])
        elif "__unimpersonate" in request.GET and 'impersonate_id' in request.session:
            del request.session['impersonate_id']
            impersonating = request.user
        if hasattr(request.user,
                   'can_impersonate') and request.user.can_impersonate and 'impersonate_id' in request.session:
            request.user = Account.objects.get(id=request.session['impersonate_id'])
            impersonating = request.user
        request.impersonating = impersonating

        response = self.get_response(request)

        return response
