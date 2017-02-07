from functools import wraps
import logging
import random
import string

from django.db import connections
from django.db import models
from django.db.models import EmailField
from django.db.models.signals import pre_migrate
from django.dispatch import receiver


# Credit: http://stackoverflow.com/questions/15624817/have-loaddata-ignore-or-disable-post-save-signals
def disable_for_loaddata(signal_handler):
    """
    Decorator that turns off signal handlers when loading fixture data.
    """

    @wraps(signal_handler)
    def wrapper(*args, **kwargs):
        if 'raw' in kwargs and kwargs['raw']:
            return
        signal_handler(*args, **kwargs)
    return wrapper


class InstanceDoesNotRequireFieldsMixin(object):
    """ Mixin that will only validate form fields that are being saved """

    def _clean_fields(self):
        if self.instance:
            for name, field in self.fields.items():
                if name not in self.data:
                    attr = getattr(self.instance, name)
                    if attr:
                        self.data[name] = attr

        return super(InstanceDoesNotRequireFieldsMixin, self)._clean_fields()

    def clean(self):
        if self.instance:
            for name, field in self.fields.items():
                if name not in self.cleaned_data:
                    attr = getattr(self.instance, name)
                    if attr:
                        self.cleaned_data[name] = attr

        return super(InstanceDoesNotRequireFieldsMixin, self).clean()


class RandomField(models.CharField):
    MAX_LOOPS = 10

    def __init__(self, seed=string.ascii_lowercase + string.digits, *args, **kwargs):
        self.seed = seed
        super(RandomField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, class_, key):
        super(RandomField, self).contribute_to_class(class_, key)
        models.signals.pre_save.connect(self.generate_unique, sender=class_)
        models.signals.post_migrate.connect(self.generate_unique, sender=class_)

    def generate_unique(self, sender, instance, *args, **kwargs):
        if not getattr(instance, self.attname):
            value = None
            for i in range(0, RandomField.MAX_LOOPS):
                value = ''.join(random.choice(self.seed) for x in range(self.max_length))
                if sender.objects.filter(**{self.name: value}).count() > 0:
                    value = None
                else:
                    break

            if i == RandomField.MAX_LOOPS:
                error = "Could not generate a unique field for field %s.%s!" % (sender._meta.module_name, self.name)
                logging.error(error)
                return
            elif i >= RandomField.MAX_LOOPS * 2/3:
                logging.warning("Looped 2/3 the max allowable loops for unique field on %s.%s consider upping the length of the keys" % (sender._meta.module_name, self.name))

            setattr(instance, self.attname, value)

#
# From https://github.com/gbourdin/django-ci-emailfield/
#

# Python 2/3 compatibility. Credit to https://github.com/oxplot/fysom/issues/1
try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str, bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring


@receiver(pre_migrate)
def setup_postgres_extensions(sender, **kwargs):
    conn = connections[kwargs['using']]
    if conn.vendor == 'postgresql':
        cursor = conn.cursor()
        cursor.execute("CREATE EXTENSION IF NOT EXISTS citext")


class CiEmailField(EmailField):
    """A case insensitive EmailField.
    It uses the CITEXT extension on postgresql and lowercases the value on
    other databases.
    """
    def db_type(self, connection):
        if connection.vendor == 'postgresql':
            return 'CITEXT'
        return super(CiEmailField, self).db_type(connection)

    def get_db_prep_value(self, value, connection, prepared=False):
        if connection.vendor != 'postgresql':
            if isinstance(value, basestring):  # value might be None
                value = value.lower()
        return super(CiEmailField, self).get_db_prep_value(
            value, connection, prepared)
