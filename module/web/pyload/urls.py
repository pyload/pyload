# -*- coding: utf-8 -*-

from os.path import join

from django.conf import settings
from django.conf.urls.defaults import *


urlpatterns = patterns('pyload',
                       (r'^home/$', 'views.home'),
                       (r'^downloads/$', 'views.downloads',{},'downloads'),
                       (r'^download/(?P<path>[a-zA-z\.0-9\-/_% "\\]+)$', 'views.download',{},'download'),
                       (r'^queue/$', 'views.queue',{}, 'queue'),
                       (r'^collector/$', 'views.collector',{}, 'collector'),
                       (r'^settings/$', 'views.config',{}, 'config'),
                       (r'^logs/$', 'views.logs',{}, 'logs'),
                       (r'^logs/(?P<item>\d+)$', 'views.logs',{}, 'logs'),
                       (r'^$', 'views.home',{}, 'home'),
                       )

urlpatterns += patterns('django.contrib.auth',
                        (r'^login/$', 'views.login', {'template_name': join(settings.TEMPLATE, 'login.html')}),
                        (r'^logout/$', 'views.logout', {'template_name': join(settings.TEMPLATE, 'logout.html')}, 'logout'),
)