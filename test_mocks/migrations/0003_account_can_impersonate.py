# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-13 15:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('test_mocks', '0002_auto_20160708_1811'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='can_impersonate',
            field=models.BooleanField(default=False, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='impersonate'),
        ),
    ]
