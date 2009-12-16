# -*- coding: utf-8 -*-
from django.contrib import admin
from models import Prefs
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as RealUserAdmin


class UserProfileInline(admin.StackedInline):
    model = Prefs

class UserAdmin(RealUserAdmin):
    inlines = [ UserProfileInline ]

admin.site.unregister(User)
admin.site.register(User, UserAdmin)