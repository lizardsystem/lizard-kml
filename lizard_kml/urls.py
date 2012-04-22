# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.contrib import admin

from lizard_ui.urls import debugmode_urlpatterns
from lizard_kml.views import *

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^kml/viewer/(?P<category_id>[0-9]*)/$', ViewerView.as_view(), name='lizard-kml-viewer'),
    url(r'^kml/viewer/$', ViewerView.as_view(), name='lizard-kml-viewer'),
    url(r'^kml/info/(?P<id>[0-9]+)/$', InfoView.as_view(), name='lizard-kml-info'),
    url(r'^kml/xls/(?P<id>[0-9]+)/$', XlsView.as_view(), name='lizard-kml-xls'),
    url(r'^kml/chart/(?P<chart_type>[-a-zA-Z0-9_]+)/(?P<id>[0-9]+)/$', ChartView.as_view(), name='lizard-kml-chart'),
    url(r'^kml/kml/(?P<kml_type>[-a-zA-Z0-9_]+)/(?P<id>[0-9]+)/$', KmlView.as_view(), name='lizard-kml-kml'),
    url(r'^kml/kml/(?P<kml_type>[-a-zA-Z0-9_]+)/$', KmlView.as_view(), name='lizard-kml-kml'),
)

urlpatterns += debugmode_urlpatterns()
