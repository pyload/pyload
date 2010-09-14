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
                        (r'^abort_link/(\d+)$', 'views.abort_link'),
                        (r'^status$', 'views.status'),
                        (r'^links$', 'views.links'), #currently active links
                       (r'^queue$', 'views.queue'),
                         (r'^pause$', 'views.pause'),
                        (r'^unpause$', 'views.unpause'),
                        (r'^cancel$', 'views.cancel'),
                        (r'^packages$', 'views.packages'),
                        (r'^package/(\d+)$', 'views.package'),
                        (r'^link/(\d+)$', 'views.link'),
                        (r'^remove_package/(\d+)$', 'views.remove_package'),
                        (r'^restart_package/(\d+)$', 'views.restart_package'),
                        (r'^remove_link/(\d+)$', 'views.remove_link'),
                        (r'^restart_link/(\d+)$', 'views.restart_link'),
                        (r'^move_package/(\d+)/(\d+)$', 'views.move_package'),
                        (r'^set_captcha$', 'views.set_captcha'),
                        (r'^package_order/([0-9|]+)$', 'views.package_order'),
                        (r'^link_order/([0-9|]+)$', 'views.link_order'),
                       )