from django.contrib import admin
from django.contrib.auth import get_user_model


Account = get_user_model()


class SlothAuthBaseUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', )

    search_fields = ['id', 'email']

    class Meta:
        model = Account
