from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    # Examples:
    url(r'^$', 'jecto.views.home', name='home'),
    url(r'home/$', 'jecto.views.home', name='home'),
    #url(r'school/$', 'jecto.views.school', name='home'),
    # url(r'^jecto/', include('jecto.foo.urls')),

    url(r'^history/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/$','jecto.views.history', name='history'),
    url(r'^zones/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/$','jecto.views.zones', name='zones'),
    url(r'^sections/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<zoneId>\d+)/$','jecto.views.sections', name='sections'),
    url(r'^inject/(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})/(?P<zoneId>\d+)/(?P<posX>\d+)/(?P<posY>\d+)/$','jecto.views.inject', name='inject'),



    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'admin/', include(admin.site.urls)),
)
