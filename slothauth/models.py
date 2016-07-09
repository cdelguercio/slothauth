from __future__ import unicode_literals

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .mail import send_mail
from .managers import UserManager
from .utils import RandomField, CiEmailField

from . import settings


class SlothAuthBaseUser(AbstractBaseUser, PermissionsMixin):

    USERNAME_FIELD = settings.ACCOUNT_NATURAL_KEY

    # AbstractBaseUser fields

    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = CiEmailField(_('email address'), unique=True)
    is_staff = models.BooleanField(_('staff status'),
                                   default=False,
                                   help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'),
                                    default=True,
                                    help_text=_('Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    # Passwordless fields

    passwordless_key = RandomField(max_length=32)
    one_time_authentication_key = RandomField(max_length=32)
    password_reset_key = RandomField(max_length=32)

    objects = UserManager()

    # Meta

    class Meta:
        abstract = True

    # Properties

    @property
    def is_passwordless(self):
        return self.passwordless_key and not self.has_usable_password()

    # Methods

    def get_short_name(self):
        return self.first_name

    def send_reset_email(self):
        from .forms import PasswordResetForm

        form = PasswordResetForm({'email': self.email})
        if form.is_valid():
            opts = {
                'text_email_template_name': 'slothauth/password_reset_email.txt',
                'html_email_template_name': 'slothauth/password_reset_email.html',
                'subject': settings.ACCOUNT_EMAIL_PASSWORD_RESET_SUBJECT,
                'css_file': 'static/css/emails/main.css',
            }
            form.save(**opts)

    def send_passwordless_login_email(self):
        if self.is_passwordless:
            context = {'domain': settings.ACCOUNT_EMAIL_DOMAIN,
                       'protocol': 'http',
                       'passwordless_key': self.passwordless_key}
            send_mail(settings.ACCOUNT_EMAIL_PASSWORDLESS_LOGIN_SUBJECT,
                      render_to_string('slothauth/passwordless_login_email.txt', context),
                      render_to_string('slothauth/passwordless_login_email.html', context),
                      settings.ACCOUNT_EMAIL_FROM,
                      self.email)
