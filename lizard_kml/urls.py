# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.contrib import admin

from lizard_ui.urls import debugmode_urlpatterns
from lizard_kml.views import KmlView, ViewerView


admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/?', include(admin.site.urls)),
    url(r'^kml/viewer/$', ViewerView.as_view(), name='lizard-kml-viewer'),
    # final backslash optional
    url(r'^kml/kml/(?P<kml_type>.*?)/(?P<id>\d+)/?$', KmlView.as_view(), name='lizard-kml-kml-id'),
    url(r'^kml/kml/(?P<kml_type>.*?)/?$', KmlView.as_view(), name='lizard-kml-kml'),
    # url(r'^something/',
    #     direct.import.views.some_method,
    #     name="name_it"),
    )
urlpatterns += debugmode_urlpatterns()
