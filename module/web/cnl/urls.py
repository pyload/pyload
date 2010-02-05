# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns('cnl',
                       # Example:
                       # (r'^pyload/', include('pyload.foo.urls')),

                       # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
                       # to INSTALLED_APPS to enable admin documentation:
                       # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                        (r'^add$', 'views.add'),
                        (r'^addcrypted$', 'views.addcrypted'),
                        (r'^addcrypted2$', 'views.addcrypted2'),
                        (r'', 'views.flash')
                       )