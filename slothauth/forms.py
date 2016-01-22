from django import forms
from django.utils.translation import gettext as _

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode

from .mail import send_mail
from .utils import InstanceDoesNotRequireFieldsMixin

from . import settings


Account = get_user_model()


class AccountForm(InstanceDoesNotRequireFieldsMixin, forms.ModelForm):
    password = forms.CharField(required=False, widget=forms.PasswordInput)

    class Meta:
        model = Account
        fields = ('email', 'password', 'first_name', 'last_name', )

    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        self.old_password = self.instance.password

    def save(self, commit=True, *args, **kwargs):
        account = super(AccountForm, self).save(commit=commit, *args, **kwargs)
        password = self.cleaned_data.get('password')
        if self.old_password != password and password:
            account.set_password(password)
        if commit:
            account.save()
        return account

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        accounts = Account.objects.filter(email=email)
        if self.instance:
            accounts = accounts.exclude(id=self.instance.id)
        if accounts.exists():
            raise forms.ValidationError(_("Email address has already been used."))
        return email

    def clean_name(self):
        return self.cleaned_data.get('name').strip()


class PasswordResetForm(forms.Form):
    error_messages = {
        'unknown': _("That email address doesn't have an associated "
                     "user account. Are you sure you've registered?"),
        'unusable': _("The user account associated with this email "
                      "address cannot reset the password."),
    }
    email = forms.EmailField(label=_("Email"), max_length=254)

    def clean_email(self):
        """
        Validates that an active user exists with the given email address.
        """
        email = self.cleaned_data["email"]
        self.users_cache = Account._default_manager.filter(email__iexact=email)
        if not len(self.users_cache):
            raise forms.ValidationError(self.error_messages['unknown'])
        if not any(user.is_active for user in self.users_cache):
            # none of the filtered users are active
            raise forms.ValidationError(self.error_messages['unknown'])
        return email

    def save(self, domain_override=None,
             subject=settings.ACCOUNT_EMAIL_PASSWORD_RESET_SUBJECT,
             text_email_template_name='password_reset_email.txt',
             html_email_template_name='password_reset_email.html',
             css_file=None,
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        """
        Generates a one-use only link for resetting password and sends to the user.
        """
        for user in self.users_cache:
            context = {
                'email': user.email,
                'uid': urlsafe_base64_encode(str(user.id)),
                'user': user,
                'token': token_generator.make_token(user),
                'domain': settings.ACCOUNT_EMAIL_DOMAIN,
                'protocol': 'http'
            }
            send_mail(subject,
                       render_to_string(text_email_template_name, context),
                       render_to_string(html_email_template_name, context),
                       settings.ACCOUNT_EMAIL_FROM,
                       user.email)
