# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserProfile(models.Model):
    """ Permissions setting """
    
    user = models.ForeignKey(User, unique=True)
    template = models.CharField(max_length=30, default='default', null=False, blank=False)

def user_post_save(sender, instance, **kwargs):
    profile, new = UserProfile.objects.get_or_create(user=instance)

models.signals.post_save.connect(user_post_save, User)