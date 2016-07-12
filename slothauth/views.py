import importlib
import re

from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth import get_user_model
from django.shortcuts import render

from rest_framework import permissions, status, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import list_route
from rest_framework.response import Response

from .serializers import AccountSerializer, BasicAccountSerializer

from . import settings


Account = get_user_model()
module_name, class_name = settings.ACCOUNT_FORM.rsplit('.', 1)
AccountForm = getattr(importlib.import_module(module_name), class_name)


class QuietBasicAuthentication(BasicAuthentication):
    # disclaimer: once the user is logged in, this should NOT be used as a
    # substitute for SessionAuthentication, which uses the django session cookie,
    # rather it can check credentials before a session cookie has been granted.
    def authenticate_header(self, request):
        return 'xBasic realm="%s"' % self.www_authenticate_realm


class BasicUserViewSet(viewsets.GenericViewSet):
    queryset = Account.objects.all()
    serializer_class = BasicAccountSerializer
    authentication_classes = (QuietBasicAuthentication, )
    permission_classes = ()


class AuthViewSet(viewsets.GenericViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    authentication_classes = (QuietBasicAuthentication, )
    permission_classes = ()

    @list_route(methods=['post'])
    def login(self, request, *args, **kwargs):

        user = authenticate(email=request.data.get('email'), username=request.data.get('username'), password=request.data.get('password'), passwordless_key=request.data.get('passwordless_key'))
        if user:
            django_login(request, user)
            return Response(AccountSerializer(request.user).data)
        elif not request.data.get('password'):
            account = Account.objects.filter(email__iexact=request.data.get('email', '').strip()).last()
            if account:
                if not account.is_passwordless:
                    # Ask them for a password
                    return Response(status=status.HTTP_412_PRECONDITION_FAILED)
                else:
                    account.send_passwordless_login_email()
                    return Response(status=status.HTTP_200_OK)
        return Response({'error': 'user not authenticated and password is given'}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'])
    def reset_password(self, request, *args, **kwargs):

        email = request.data.get('email', '').strip().lower()
        account = Account.objects.filter(email=email).last()
        if account:
            account.send_reset_email()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)

    @list_route(methods=['post'])
    def signup(self, request, *args, **kwargs):

        form = AccountForm(data=request.data)
        if form.is_valid():
            form.save()

            # Force the login
            user = authenticate(passwordless_key=form.instance.passwordless_key, force=True)
            django_login(request, user)

            user.save()
            return Response(AccountSerializer(request.user).data)
        return Response({'error': form.errors}, status=status.HTTP_412_PRECONDITION_FAILED)

    @list_route(methods=['post', 'delete'])
    def logout(self, request, *args, **kwargs):

        django_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountViewSet(viewsets.GenericViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )

    @list_route(methods=['get', 'post', 'patch'], permission_classes=(permissions.IsAuthenticated, ))
    def me(self, request, *args, **kwargs):

        if request.method == 'PATCH':
            form = AccountForm(instance=request.user, data=request.data)
            if form.is_valid():
                form.save()
                return Response(AccountSerializer(request.user).data)
            return Response({'error': form.errors}, status=status.HTTP_412_PRECONDITION_FAILED)
        return Response(AccountSerializer(request.user).data)

    ###
    # change_email
    #  currently requires a password to work
    ###
    @list_route(methods=['post', 'patch'])
    def change_email(self, request, *args, **kwargs):

        if 'email' not in request.data or 'confirm_email' not in request.data or 'password' not in request.data:
            return Response({'error': 'EMAIL MISSING'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(request.data['password']):
            return Response({'error': 'BAD PASSWORD'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.data['email'].strip().lower() == request.data['confirm_email'].strip().lower():
            return Response({'error': 'EMAIL MISMATCH'}, status=status.HTTP_400_BAD_REQUEST)

        if not re.match(r"[^@]+@[^@]+\.[^@]+", request.data['email']):
            return Response({'error': 'EMAIL INVALID'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.email = request.data['email'].strip()
        request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    ###
    # change_password
    #  currently requires a password to work
    ###
    @list_route(methods=['post', 'patch'])
    def change_password(self, request, *args, **kwargs):

        # Ensure that we are either testing the current_password, or the password_reset_key
        if 'password' not in request.data or 'password_repeat' not in request.data or\
           ('current_password' not in request.data and 'password_reset_key' not in request.data):
            return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)

        if request.data['password'] != request.data['password_repeat']:
            return Response({'error': 'Password mismatch'}, status=status.HTTP_400_BAD_REQUEST)

        # Test current_password
        if 'current_password' in request.data and not request.user.check_password(request.data['current_password']):
            return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)

        # Or test password_reset_key
        if 'password_reset_key' in request.data and not request.data.get('password_reset_key') == request.user.password_reset_key:
            return Response({'error': 'Incorrect password reset key'}, status=status.HTTP_400_BAD_REQUEST)

        # If the password_reset_key was attempted to be used, then reset it
        if 'password_reset_key' in request.data and not request.data.get('password_reset_key') == '':
            request.user.password_reset_key = Account._meta.get_field('password_reset_key').generate_unique(instance=request.user, sender=Account)

        request.user.set_password(request.data['password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['post', 'patch'])
    def change_settings(self, request, *args, **kwargs):

        if 'first_name' in request.data:
            request.user.first_name = request.data['first_name']
        if 'last_name' in request.data:
            request.user.last_name = request.data['last_name']

        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


def signup(request):
    return render(request, 'slothauth/signup.html')


def login(request):
    return render(request, 'slothauth/login.html')


def password_reset(request):
    return render(request, 'slothauth/password_reset.html')


def change_email(request):
    return render(request, 'slothauth/change_email.html')


def passwordless_check_email(request):
    return render(request, 'slothauth/passwordless_check_email.html')


def profile(request):
    return render(request, 'slothauth/profile.html', context={'email': request.user.email})


def logout(request):
    return render(request, 'slothauth/logout.html')


def passwordless_signup(request):
    return render(request, 'slothauth/passwordless_signup.html')


def passwordless_login(request):
    return render(request, 'slothauth/passwordless_login.html')
