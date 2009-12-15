from django.conf.urls.defaults import *

urlpatterns = patterns('',
                       (r'^login/$', 'pyload.views.login'),
                       (r'^home/$', 'pyload.views.home'),
                       (r'^test/$', 'pyload.views.home'),
)
