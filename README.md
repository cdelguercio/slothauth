# SlothAuth

SlothAuth is a Django app for adding user authentication and accounts with the follow features:

- Signup
- Login
- Logout
- Passwordless Authentication
- Passwordless Login via Email
- Add Password to Passwordless Account
- User Impersonation for Admins
- Password Reset
- Change email

SlothAuth is meant to be programmer friendly. It doesn't sets things up for you and each component can be easily overridden.

SlothAuth 0.7.2 and above have been tested with Django 1.10.x and Python 3.5

Earlier versions tested with Django 1.9.x and Python 2.7

## Credit

SlothAuth was authored by Chris Del Guercio and Shane Zilinskas

## Installation

```
pip install slothauth
```

## Updating SlothAuth

Since SlothAuth's SlothAuthBaseUser is abstract, it might be necessary to run makemigrations on your user account app after updating SlothAuth.

## Usage

When DEBUG == True, including the slothauth URLs will give you the following debug URLs which are attached to some unstyled template forms:
```
r'^signup/?'
r'^login/?'
r'^password_reset/?'
r'^change_email/?'
r'^profile/?'
r'^logout/?'
r'^passwordless_signup/?'
r'^passwordless_login/?'
```

Note: These URLs will only work if you named your user model "Account"

## Quick Start

1) Add slothauth, rest_framework, and rest_framework.authtoken to your INSTALLED_APPS in your project's settings.py file:
```
INSTALLED_APPS += [
    'slothauth',
    'rest_framework',
    'rest_framework.authtoken',
]
```

2) Add the following to your project's urls.py file:
```
from django.conf.urls import url, include
import slothauth.urls as slothauth_urls

urlpatterns = [
    ### your other urls here ###
    url(r'^', include(slothauth_urls)),
]
```

3) Add the Passwordless User middleware to your settings.py file:
```
MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'slothauth.middleware.PasswordlessUserMiddleware',
    'slothauth.middleware.OneTimeAuthenticationKeyMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

4) Add the SlothAuth Authentication Backend to your settings.py file:
```
AUTHENTICATION_BACKENDS = [
    'slothauth.backends.PasswordlessAuthentication',
    'django.contrib.auth.backends.ModelBackend',
]
```

5) Create a subclass of SlothAuthBaseUser in the model file of your User/Account app:
```
from slothauth.models import SlothAuthBaseUser

class Account(SlothAuthBaseUser):
    # add custom fields here, or just put 'pass'
```

Note: You can name this model whatever you'd like, but the Slothauth debug URLs will only work if you name it "Account".

Add your app to INSTALLED_APPS

```
INSTALLED_APPS += [
    'your_app',
]
```

Be sure to make a migration for your app and run it
```
python manage.py makemigrations
python manage.py migrate your_app
```

6) Make sure that your AUTH_USER_MODEL setting is set to your subclass of SlothAuthBaseUser:
```
AUTH_USER_MODEL = 'your_app.Account'
```

7) Run the SlothAuth migration
```
python manage.py migrate slothauth
```

8) (Optional) Add the Impersonate Middleware to your settings.py file:
```
MIDDLEWARE_CLASSES += [
    'slothauth.middleware.ImpersonateMiddleware',
]
```

9) (Optional) Set up email in your settings.py file. You can set up a gmail account to use for testing as long as you turn
"Allow less secure apps" at https://myaccount.google.com/security#connectedapps to "ON". If it still doesn't work, try
visiting https://accounts.google.com/DisplayUnlockCaptcha. It should fix it within 15 minutes. A lot of times, Gmail
will continuously ban your account and you have to keep visiting that to unban yourself.
```
EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'your_email@gmail.com'
EMAIL_HOST_PASSWORD = 'your_password'
DEFAULT_FROM_EMAIL = 'your_email@gmail.com'

ACCOUNT_EMAIL_DOMAIN = 'example.com'
ACCOUNT_EMAIL_FROM = 'example@example.com'
ACCOUNT_EMAIL_PASSWORD_RESET_SUBJECT = 'Password Reset'
ACCOUNT_EMAIL_PASSWORDLESS_LOGIN_SUBJECT = 'Your Login Link'
```

9) (Optional) Override the AccountForm in your account forms file and add the ACCOUNT_FORM value in your settings.py file:
```
from slothauth.forms import AccountForm

class CustomAccountForm(AccountForm):
```

```
ACCOUNT_FORM = 'your_app.forms.CustomAccountForm'
```

## Running Tests

1) Install dependencies

```
pip3 install factory_boy
```

2) Run tests

```
python3 run_tests.py
```
