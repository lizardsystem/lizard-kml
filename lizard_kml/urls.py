# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.contrib import admin

from lizard_map.views import HomepageView
from lizard_kml.views import KmlView, ViewerView
from lizard_ui.urls import debugmode_urlpatterns

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', HomepageView.as_view()),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^map/', include('lizard_map.urls')),
    url(r'^ui/', include('lizard_ui.urls')),
    url(r'^kml/viewer/(?P<kml_type_id>.*)$', ViewerView.as_view(), name='lizard_kml.viewer'),
    #url(r'^kml/$',                ViewerView.as_view(), name='lizard_kml.viewer'),
    url(r'^kml/kml/(?P<area_id>.*)/$', KmlView.as_view(),    name='lizard_kml.kml'),
    # url(r'^something/',
    #     direct.import.views.some_method,
    #     name="name_it"),
    )
urlpatterns += debugmode_urlpatterns()
