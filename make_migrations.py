#!/usr/bin/env python

# Based on Stack Overflow answer: http://stackoverflow.com/questions/30656162/migrations-in-stand-alone-django-app

import os
import sys
import django

from django.conf import settings
from django.core.management import call_command

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

settings.configure(
    DEBUG=True,
    INSTALLED_APPS=(
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'rest_framework.authtoken',
        'slothauth',
        'test_mocks',
    ),
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    },
    ROOT_URLCONF = 'slothauth.urls',
    MIDDLEWARE_CLASSES=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'slothauth.middleware.PasswordlessUserMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ],
    AUTHENTICATION_BACKENDS=[
        'slothauth.backends.PasswordlessAuthentication',
    ],
)

django.setup()
call_command('makemigrations', 'slothauth')
call_command('makemigrations', 'test_mocks')

