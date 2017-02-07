from django.core import mail
from django.test import TestCase


from ..factories import AccountFactory, PasswordlessAccountFactory


class AccountModelTest(TestCase):

    def test_send_passwordless_login_email(self):
        account = AccountFactory()
        account.set_password('password')
        account.save()

        account.send_passwordless_login_email()

        self.assertEqual(len(mail.outbox), 0)

        passwordless_account = PasswordlessAccountFactory()

        self.assertTrue(passwordless_account.is_passwordless)

        passwordless_account.send_passwordless_login_email()

        self.assertEqual(len(mail.outbox), 1)
