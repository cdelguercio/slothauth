import json

from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core import mail
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from .utils import obj_is
from .api_utils import is_user_me

from ..factories import AccountFactory

from .. import settings

Account = get_user_model()


class PasswordlessAuthTest(TestCase):

    ACCOUNT_PASSWORD = 'test'

    def setUp(self, *args, **kwargs):
        super(TestCase, self).setUp(*args, **kwargs)

        self.account_1 = Account(email='test1@taggler.com')
        self.account_1.set_password(self.ACCOUNT_PASSWORD)
        self.account_1.save()

        self.passwordless = Account(email='passwordless@taggler.com')
        self.passwordless.save()

    def test_email_password_auth(self):
        self.assertTrue(authenticate(email=self.account_1.email, password=self.ACCOUNT_PASSWORD))

    def test_email_password_fails_for_wrong_password(self):
        self.assertFalse(authenticate(email=self.account_1.email, password=self.ACCOUNT_PASSWORD*2))

    def test_email_password_fails_for_wrong_email(self):
        self.assertFalse(authenticate(email=self.account_1.email*2, password=self.ACCOUNT_PASSWORD))

    def test_email_password_fails_for_wrong_password_and_email(self):
        self.assertFalse(authenticate(email=self.account_1.email*2, password=self.ACCOUNT_PASSWORD*2))

    def test_email_password_fails_for_blank_email(self):
        self.assertFalse(authenticate(email='', password=''))

    def test_passwordless_auth(self):
        self.assertTrue(authenticate(passwordless_key=self.passwordless.passwordless_key))

    def test_passwordless_auth_fails_for_registered_users(self):
        self.assertFalse(authenticate(passwordless_key=self.account_1.passwordless_key))

    def test_is_passwordless_property(self):
        self.assertTrue(self.passwordless.is_passwordless, msg="Passwordless user is not correctly detected")
        self.assertFalse(self.account_1.is_passwordless, msg="User with password is incorrectly flagged as passwordless")

    def test_passwordless_login_middleware(self):
        c = Client()

        def get_sessionid(response):
            return response.cookies.get('sessionid').value

        # Verify we don't have a cookie set when hitting the login page without login
        response = c.get('/login')
        self.assertIsNone(response.cookies.get('sessionid'))

        # Verify the cookie is set after hitting the homepage with a passwordless login
        response = c.get('/login', {settings.PASSWORDLESS_GET_PARAM: self.account_1.passwordless_key})
        session = Session.objects.get(session_key=get_sessionid(response))
        uid = session.get_decoded().get('_auth_user_id')
        users = Account.objects.filter(pk=uid)
        self.assertEqual(users.count(), 1)


class OneTimeAuthenticationKeyAuthTest(TestCase):

    ACCOUNT_PASSWORD = 'test'

    def setUp(self, *args, **kwargs):
        super(TestCase, self).setUp(*args, **kwargs)

        self.account_1 = Account(email='test1@taggler.com')
        self.account_1.set_password(self.ACCOUNT_PASSWORD)
        self.account_1.save()

    def test_one_time_authentication_key_middleware(self):
        c = Client()

        def get_sessionid(response):
            return response.cookies.get('sessionid').value

        # Verify we don't have a cookie set when hitting the login page without login
        response = c.get('/login')
        self.assertIsNone(response.cookies.get('sessionid'))

        # Save one time authentication key
        one_time_authentication_key = self.account_1.one_time_authentication_key

        # Verify the cookie is set after hitting the homepage with a one time authentication key
        response = c.get('/login', {settings.ONE_TIME_AUTHENTICATION_KEY_GET_PARAM: one_time_authentication_key})
        session = Session.objects.get(session_key=get_sessionid(response))
        uid = session.get_decoded().get('_auth_user_id')
        users = Account.objects.filter(pk=uid)
        self.assertEqual(users.count(), 1)

        # Check that one time authentication key changed upon use
        self.assertNotEqual(users[0].one_time_authentication_key, one_time_authentication_key)


class SignupEmailTest(TestCase):

    ACCOUNT_EMAIL = 'customer@taggler.com'
    ACCOUNT_PASSWORD = 'password'

    def test_signup_email_sent(self):

        self.account = Account(email=self.ACCOUNT_EMAIL)
        self.account.set_password(self.ACCOUNT_PASSWORD)
        self.account.save()

        self.assertTrue(authenticate(email=self.account.email, password=self.ACCOUNT_PASSWORD))


class ApiAuthTest(TestCase):

    def setUp(self):
        super(ApiAuthTest, self).setUp()

        self.client = APIClient()
        self.email = 'shane@clearsumm.it'
        self.password = 'ultrapress'

    def test_auth_login(self):
        self.test_auth_signup_with_password()

        response = self.client.post(reverse('account-login'), data={'email': self.email, 'password': self.password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=str(response.status_code) + ': ' + response.content)

        content = response.content

        self.assertTrue(obj_is(content, is_user_me), msg=content)

    def test_auth_login_with_wrong_password(self):
        self.test_auth_signup_with_password()

        response = self.client.post(reverse('account-login'), data={'email': self.email, 'password': self.password*2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.status_code)

    def test_auth_signup_passwordless(self):
        response = self.client.post(reverse('account-signup'), data={'email': self.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=str(response.status_code) + ': ' + response.content)

        content = response.content

        self.assertTrue(obj_is(content, is_user_me), msg=content)
        account = Account.objects.get(email=self.email)
        self.assertTrue(account.is_passwordless)

    def test_auth_signup_email_taken(self):
        self.test_auth_signup_passwordless()

        response = self.client.post(reverse('account-signup'), data={'email': self.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_412_PRECONDITION_FAILED, msg=str(response.status_code) + ': ' + response.content)

    def test_auth_signup_with_password(self):
        response = self.client.post(reverse('account-signup'), data={'email': self.email, 'password': self.password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=str(response.status_code) + ': ' + response.content)

        content = response.content

        self.assertTrue(obj_is(content, is_user_me), msg=content)
        account = Account.objects.get(email=self.email)
        self.assertFalse(account.is_passwordless)

    def test_auth_logout(self):
        response = self.client.delete(reverse('account-logout'), format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, msg=str(response.status_code) + ': ' + response.content)

    def test_password_reset(self):

        # check that non-existant email sends back an error
        response = self.client.post(reverse('account-reset-password'), data={'email': self.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, msg=str(response.status_code) + ': ' + response.content)
        self.assertEqual(len(mail.outbox), 0)

        # check that existing email sends back a good response and sends an email
        account = AccountFactory(email=self.email)
        num_emails = len(mail.outbox)
        response = self.client.post(reverse('account-reset-password'), data={'email': account.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, msg=str(response.status_code) + ': ' + response.content + ': ' + str(account.email))
        self.assertEqual(len(mail.outbox), num_emails + 1)

    def test_change_email(self):
        NEW_EMAIL = 'asdasfasdf@adsfasf.com'
        NEW_MISMATCH_EMAIL = NEW_EMAIL + 'd'
        NEW_FAIL_EMAIL = 'adsfasdfasdfasdf'
        WRONG_PASSWORD = self.password + '1'

        self.test_auth_signup_with_password()

        account = Account.objects.all()[0]

        self.assertEqual(account.email, self.email)

        # check that change email works when email and confirm_email are the same
        header = {'HTTP_AUTHORIZATION': 'Token {}'.format(Token.objects.get(user=account).key)}

        response = self.client.patch('/api/v1/accounts/change_email/', data={'email': NEW_EMAIL, 'confirm_email': NEW_EMAIL, 'password': self.password}, format='json', **header)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, msg=str(response.status_code) + ': ' + response.content)

        account = Account.objects.all()[0]

        self.assertEqual(account.email, NEW_EMAIL)

        # check that change email failed when email and confirm_email are different
        header = {'HTTP_AUTHORIZATION': 'Token {}'.format(Token.objects.get(user=account).key)}

        response = self.client.patch('/api/v1/accounts/change_email/', data={'email': NEW_MISMATCH_EMAIL, 'confirm_email': NEW_EMAIL, 'password': self.password}, format='json', **header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=str(response.status_code) + ': ' + response.content)
        content = json.loads(response.content)
        self.assertEqual(content['error'], "EMAIL MISMATCH")

        account = Account.objects.all()[0]

        self.assertNotEqual(account.email, NEW_MISMATCH_EMAIL)
        self.assertEqual(account.email, NEW_EMAIL)

        # check that change email failed when email is invalid
        header = {'HTTP_AUTHORIZATION': 'Token {}'.format(Token.objects.get(user=account).key)}

        response = self.client.patch('/api/v1/accounts/change_email/', data={'email': NEW_FAIL_EMAIL, 'confirm_email': NEW_FAIL_EMAIL, 'password': self.password}, format='json', **header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=str(response.status_code) + ': ' + response.content)
        content = json.loads(response.content)
        self.assertEqual(content['error'], "EMAIL INVALID")

        account = Account.objects.all()[0]

        self.assertNotEqual(account.email, NEW_FAIL_EMAIL)
        self.assertEqual(account.email, NEW_EMAIL)

        # check that change email failed when password is invalid
        header = {'HTTP_AUTHORIZATION': 'Token {}'.format(Token.objects.get(user=account).key)}

        response = self.client.patch('/api/v1/accounts/change_email/', data={'email': NEW_FAIL_EMAIL, 'confirm_email': NEW_FAIL_EMAIL, 'password': WRONG_PASSWORD}, format='json', **header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=str(response.status_code) + ': ' + response.content)
        content = json.loads(response.content)
        self.assertEqual(content['error'], "BAD PASSWORD")

        account = Account.objects.all()[0]

        self.assertNotEqual(account.email, NEW_FAIL_EMAIL)
        self.assertEqual(account.email, NEW_EMAIL)

        # check that change email failed when email isn't sent
        header = {'HTTP_AUTHORIZATION': 'Token {}'.format(Token.objects.get(user=account).key)}

        response = self.client.patch('/api/v1/accounts/change_email/', data={}, format='json', **header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=str(response.status_code) + ': ' + response.content)
        content = json.loads(response.content)
        self.assertEqual(content['error'], "EMAIL MISSING")

        account = Account.objects.all()[0]

        self.assertEqual(account.email, NEW_EMAIL)

    def test_change_password(self):

        NEW_PASSWORD = self.password + '1'
        BAD_PASSWORD_REPEAT = NEW_PASSWORD + '2'
        WRONG_PASSWORD = self.password + '3'

        self.test_auth_signup_with_password()

        account = Account.objects.all()[0]

        self.assertEqual(account.email, self.email)

        # check that sending the wrong current password fails
        header = {'HTTP_AUTHORIZATION': 'Token {}'.format(Token.objects.get(user=account).key)}

        response = self.client.patch('/api/v1/accounts/change_password/', data={'current_password': WRONG_PASSWORD, 'password': NEW_PASSWORD, 'password_repeat': NEW_PASSWORD}, format='json', **header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=str(response.status_code) + ': ' + response.content)

        account = Account.objects.all()[0]

        self.assertTrue(account.check_password(self.password))

        # check that sending mismatching new passwords fails
        header = {'HTTP_AUTHORIZATION': 'Token {}'.format(Token.objects.get(user=account).key)}

        response = self.client.patch('/api/v1/accounts/change_password/', data={'current_password': self.password, 'password': NEW_PASSWORD, 'password_repeat': BAD_PASSWORD_REPEAT}, format='json', **header)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, msg=str(response.status_code) + ': ' + response.content)

        account = Account.objects.all()[0]

        self.assertTrue(account.check_password(self.password))

        # check that sending matching new passwords and the correct current password succeeds
        header = {'HTTP_AUTHORIZATION': 'Token {}'.format(Token.objects.get(user=account).key)}

        response = self.client.patch('/api/v1/accounts/change_password/', data={'current_password': self.password, 'password': NEW_PASSWORD, 'password_repeat': NEW_PASSWORD}, format='json', **header)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, msg=str(response.status_code) + ': ' + response.content)

        account = Account.objects.all()[0]

        self.assertTrue(account.check_password(NEW_PASSWORD))
