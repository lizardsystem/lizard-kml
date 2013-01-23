import logging
import os

from django.conf import settings
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.contrib import admin
from django.shortcuts import redirect

from lizard_ui.urls import debugmode_urlpatterns

from lizard_kml.views import *
from lizard_kml.jarkus.views import *
from lizard_kml.api import *

logger = logging.getLogger(__name__)

# ensure NC_RESOURCE points to an existing file to avoid developer confusion
if not (settings.NC_RESOURCE['transect'].startswith('http') or os.path.isfile(settings.NC_RESOURCE['transect'])):
    logger.warn('Be sure to point NC_RESOURCE to some valid files in your settings.')

def to_viewer(request):
    return redirect('lizard-kml-viewer')

urlpatterns = patterns(
    '',
    url(r'^$', to_viewer, name='lizard-kml-root'),
    url(r'^viewer/$', ViewerView.as_view(), name='lizard-kml-viewer'),
    url(r'^jarkuskml/(?P<kml_type>[-a-zA-Z0-9_]+)/(?P<id>[0-9]+)/$', JarkusKmlView.as_view(), name='lizard-jarkus-kml'),
    url(r'^jarkuskml/(?P<kml_type>[-a-zA-Z0-9_]+)/$', JarkusKmlView.as_view(), name='lizard-jarkus-kml'),
    url(r'^info/(?P<id>[0-9]+)/$', InfoView.as_view(), name='lizard-kml-info'),
    url(r'^xls/(?P<id>[0-9]+)/$', XlsView.as_view(), name='lizard-kml-xls'),
    url(r'^chart/(?P<chart_type>[-a-zA-Z0-9_]+)/$', ChartView.as_view(), name='lizard-kml-chart'),
    url(r'^chart/(?P<chart_type>[-a-zA-Z0-9_]+)/(?P<id>[0-9]+)/$', ChartView.as_view(), name='lizard-kml-chart'),
    url(r'^kml/(?P<kml_resource_id>[0-9]+)/$', KmlResourceView.as_view(), name='lizard-kml-kml'),
    url(r'^api/$', CategoryTreeView.as_view(), name='lizard-kml-api'),
)

if getattr(settings, 'LIZARD_KML_STANDALONE', False):
    admin.autodiscover()
    urlpatterns += patterns(
        '',
        (r'^admin/', include(admin.site.urls)),
    )
    urlpatterns += debugmode_urlpatterns()
