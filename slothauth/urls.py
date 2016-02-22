from django.conf.urls import include, url

from rest_framework.routers import DefaultRouter

from .views import change_email, login, logout, password_reset, profile, signup, passwordless_signup,\
                   passwordless_login, AccountViewSet, AuthViewSet

from . import settings

router = DefaultRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'accounts/auth', AuthViewSet)

urlpatterns = [
    url(r'^api/' + settings.API_VERSION + '/', include(router.urls)), # TODO makes sense to have a settings.API_BASE_URL rather than a settings.API_VERSION?
    url(r'^signup/?', signup, name='signup'),
    url(r'^login/?', login, name='login'),
    url(r'^password_reset/?', password_reset, name='password_reset'),
    url(r'^change_email/?', change_email, name='change_email'),
    url(r'^profile/?', profile, name='profile'),
    url(r'^logout/?', logout, name='logout'),
    url(r'^passwordless_signup/?', passwordless_signup, name='passwordless_signup'),
    url(r'^passwordless_login/?', passwordless_login, name='passwordless_login'),
    #(r'^password-reset-done/$', 'django.contrib.auth.views.password_reset_complete'),
    #(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm',
    #        {'post_reset_redirect' : '/password-reset-done/'}),
]

# TODO create setting for turning on and off debug urls
