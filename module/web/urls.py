# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings

from os.path import join

admin.autodiscover()

urlpatterns = patterns('',
                       # Example:
                       # (r'^pyload/', include('pyload.foo.urls')),

                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
                       # to INSTALLED_APPS to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                        (r'^admin/', include(admin.site.urls)),
                       #(r'^json/', include(ajax.urls)),
                        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
                         {'document_root': settings.MEDIA_ROOT}),
                       (r'^login/$', 'django.contrib.auth.views.login', {'template_name': join(settings.TEMPLATE,'login.html')}),
                       (r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': join(settings.TEMPLATE,'logout.html')}),
                       (r'^home/$', 'pyload.views.home'),
                       (r'^downloads/$', 'pyload.views.downloads'),
                       (r'^queue/$', 'pyload.views.queue'),
                       (r'^logs/$', 'pyload.views.logs'),
                       (r'^$', 'pyload.views.home'),
                       )
