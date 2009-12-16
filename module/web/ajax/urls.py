# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings


urlpatterns = patterns('ajax',
                       # Example:
                       # (r'^pyload/', include('pyload.foo.urls')),

                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
                       # to INSTALLED_APPS to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                        (r'^add_package$', 'views.add_package'),
                        (r'^status$', 'views.status'),
                        (r'^links$', 'views.links'),
                       (r'^queue$', 'views.queue'),
                         (r'^pause$', 'views.pause'),
                        (r'^unpause$', 'views.unpause'),
                       )