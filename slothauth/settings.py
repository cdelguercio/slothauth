import warnings

from django.conf import settings

if not hasattr(settings, 'AUTH_USER_MODEL') or getattr(settings, 'AUTH_USER_MODEL') == 'auth.User':
    warnings.warn('User must set \'AUTH_USER_MODEL\' to a subclass of \'slothauth.SlothAuthBaseUser\' in project settings. Check that no other apps are editing the value of \'AUTH_USER_MODEL\'.')

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL')

ACCOUNT_NATURAL_KEY = getattr(settings, 'ACCOUNT_NATURAL_KEY', 'email')

PASSWORDLESS_GET_PARAM = getattr(settings, 'PASSWORDLESS_GET_PARAM', 'key')

ONE_TIME_AUTHENTICATION_KEY_GET_PARAM = getattr(settings, 'ONE_TIME_AUTHENTICATION_KEY_GET_PARAM', 'otk')

API_VERSION = getattr(settings, 'API_VERSION', 'v1')

ACCOUNT_FORM = getattr(settings, 'ACCOUNT_FORM', 'slothauth.forms.AccountForm')

# Domain for links in email templates
ACCOUNT_EMAIL_DOMAIN = getattr(settings, 'ACCOUNT_EMAIL_DOMAIN', 'example.com')

ACCOUNT_EMAIL_FROM = getattr(settings, 'ACCOUNT_EMAIL_FROM', 'example@example.com')

ACCOUNT_EMAIL_PASSWORD_RESET_SUBJECT = getattr(settings, 'ACCOUNT_EMAIL_PASSWORD_RESET_SUBJECT', 'Password Reset')

ACCOUNT_EMAIL_PASSWORDLESS_LOGIN_SUBJECT = getattr(settings, 'ACCOUNT_EMAIL_PASSWORDLESS_LOGIN_SUBJECT', 'Your Login Link')

# Authentication

AUTHENTICATION_BACKENDS = [
    'slothauth.backends.PasswordlessAuthentication',
]

# Django Rest Framework

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 9999,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAdminUser',
    ),
}
