
from os.path import join

from django.conf import settings
from django.conf.urls.defaults import *


urlpatterns = patterns('pyload',
                       (r'^home/$', 'views.home'),
                       (r'^downloads/$', 'views.downloads',{},'downloads'),
                       (r'^queue/$', 'views.queue',{}, 'queue'),
                       (r'^logs/$', 'views.logs',{}, 'logs'),
                       (r'^$', 'views.home',{}, 'home'),
                       )

urlpatterns += patterns('django.contrib.auth',
                        (r'^login/$', 'views.login', {'template_name': join(settings.TEMPLATE, 'login.html')}),
                        (r'^logout/$', 'views.logout', {'template_name': join(settings.TEMPLATE, 'logout.html')}, 'logout'),
)