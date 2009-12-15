# -*- coding: utf-8 -*-
from django.db import models
#from django.contrib.auth.models.User import User as UserProfile
# Create your models here.


class Perm(models.Model):
    """ extended pyLoad user Profile """
    
    #user = models.ForeignKey(UserProfile, unique=True)
    #template = models.CharField(maxlength=30)
    
    class Meta:
        permissions = (
            ("can_see_dl", "Can see Downloads"),
            ("can_add", "Can add Downloads"),
            ("can_delete", "Can delete Downloads"),
            ("can_download", "Can download Files"),
            ("can_see_logs", "Can see logs"),
            ("can_change_status", "Can change status"),
        )