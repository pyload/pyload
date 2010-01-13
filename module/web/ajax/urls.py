# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns('ajax',
                       # Example:
                       # (r'^pyload/', include('pyload.foo.urls')),

                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
                       # to INSTALLED_APPS to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                        (r'^add_package$', 'views.add_package'),
                        (r'^remove_link/(\d+)$', 'views.remove_link'),
                        (r'^status$', 'views.status'),
                        (r'^links$', 'views.links'), #currently active links
                       (r'^queue$', 'views.queue'),
                         (r'^pause$', 'views.pause'),
                        (r'^unpause$', 'views.unpause'),
                        (r'^packages$', 'views.packages'),
                        (r'^package/(\d+)$', 'views.package'),
                        (r'^link/(\d+)$', 'views.link'),
                       )