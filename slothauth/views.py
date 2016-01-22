import re

from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth import get_user_model
from django.shortcuts import render_to_response
from django.template import RequestContext

from rest_framework import permissions, status, viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response


from .forms import AccountForm
from .serializers import AccountSerializer, BasicAccountSerializer


Account = get_user_model()


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
                    return Response(status=418)
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

        if not request.user.is_authenticated():
            email = request.data.get('email', '').strip().lower()
            accounts = Account.objects.filter(email=email)
            if accounts.count() == 0:

                form = AccountForm(data=request.data)
                if form.is_valid():
                    form.save()

                    # Force the login
                    user = authenticate(passwordless_key=form.instance.passwordless_key, force=True)
                    django_login(request, user)

                    user.save()
                    return Response(AccountSerializer(request.user).data)
                return Response({'error': form.errors}, status=status.HTTP_412_PRECONDITION_FAILED)
            else:
                account = accounts.last()
                if account.is_passwordless:
                    # send login email
                    return Response(BasicAccountSerializer(account).data, status=status.HTTP_403_FORBIDDEN)
                else:
                    # is password account - tell interface to present password prompt
                    return Response(status=status.HTTP_409_CONFLICT)

        return Response(status=status.HTTP_409_CONFLICT)

    @list_route(methods=['post', 'delete'])
    def logout(self, request, *args, **kwargs):
        django_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountViewSet(viewsets.GenericViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )

    @list_route(methods=['get', 'post', 'patch'])
    def me(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if request.method == 'PATCH':
            form = AccountForm(instance=request.user, data=request.data)
            if form.is_valid():
                form.save()
                return Response(AccountSerializer(request.user).data)
            return Response({'error': form.errors}, status=status.HTTP_412_PRECONDITION_FAILED)
        return Response(AccountSerializer(request.user).data)

    @list_route(methods=['post', 'patch'])
    def change_email(self, request, *args, **kwargs):

        if 'email' in request.data and 'confirm_email' in request.data:
            if request.data['email'].strip().lower() == request.data['confirm_email'].strip().lower():
                if re.match(r"[^@]+@[^@]+\.[^@]+", request.data['email']):
                    request.user.email = request.data['email'].strip()
                    request.user.save()

                    return Response(status=status.HTTP_204_NO_CONTENT)

                return Response({'error': 'EMAIL INVALID'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': 'EMAIL MISMATCH'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'EMAIL MISSING'}, status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post', 'patch'])
    def change_password(self, request, *args, **kwargs):
        if 'password' not in request.data or 'password_repeat' not in request.data:
            return Response({'error': 'Missing fields'}, status=status.HTTP_400_BAD_REQUEST)
        if request.data['password'] != request.data['password_repeat']:
            return Response({'error': 'Password mismatch'}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(request.data['password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


def signup(request):
    return render_to_response('slothauth/signup.html', context_instance=RequestContext(request))


def login(request):
    return render_to_response('slothauth/login.html', context_instance=RequestContext(request))


def password_reset(request):
    return render_to_response('slothauth/password_reset.html', context_instance=RequestContext(request))


def change_email(request):
    return render_to_response('slothauth/change_email.html', context_instance=RequestContext(request))


def passwordless_check_email(request):
    return render_to_response('slothauth/passwordless_check_email.html', context_instance=RequestContext(request))


def profile(request):
    return render_to_response('slothauth/profile.html', context_instance=RequestContext(request, {'email': request.user.email}))


def logout(request):
    return render_to_response('slothauth/logout.html', context_instance=RequestContext(request))


def passwordless_signup(request):
    return render_to_response('slothauth/passwordless_signup.html', context_instance=RequestContext(request))


def passwordless_login(request):
    return render_to_response('slothauth/passwordless_login.html', context_instance=RequestContext(request))
