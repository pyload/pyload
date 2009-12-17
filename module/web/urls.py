# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings

from os.path import join

admin.autodiscover()

urlpatterns = patterns('',
                       # Example:

                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
                       # to INSTALLED_APPS to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       (r'^admin/', include(admin.site.urls)), # django 1.0 not working
                       (r'^json/', include('ajax.urls')),
                        (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/img/favicon.ico'}),
                        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
                         {'document_root': settings.MEDIA_ROOT}),
                       (r'^', include('pyload.urls')),
                       )
