# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Prefs(models.Model):
    """ Permissions setting """
    
    user = models.ForeignKey(User, unique=True)
    template = models.CharField(max_length=30, default='default', null=False, blank=False) #@TODO: currently unused
        
    class Meta:
        permissions = (
            ('can_see_dl', 'User can see Downloads'),
            ('can_change_status', 'User can change Status'),
            ('can_download', 'User can download'),
            ('can_add', 'User can add Links'),
            ('can_delete', 'User can delete Links'),
            ('can_see_logs', 'User can see Logs'),
        )
        verbose_name = "Preferences"
        verbose_name_plural = "Preferences"
    
    def __unicode__(self):
        return "Preferences for %s" % self.user


def user_post_save(sender, instance, **kwargs):
    profile, new = Prefs.objects.get_or_create(user=instance)

models.signals.post_save.connect(user_post_save, User)