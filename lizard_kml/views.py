# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.gis.shortcuts import render_to_kmz, compress_kml

from lizard_map.views import AppView, WorkspaceEditMixin, CollageMixin, ViewContextMixin, GoogleTrackingMixin, TemplateView, CrumbsMixin

from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
from lxml import etree

from lizard_kml.models import KmlType, Area

class AppView2(WorkspaceEditMixin, CollageMixin, ViewContextMixin, GoogleTrackingMixin, TemplateView, CrumbsMixin):
    pass

class KmlView(View):
    """
    Renders a dynamic KML file.
    """

    def get(self, request, area_id=None):
        # "build" requested KML datastructure
        key_to_range = {1: 6300, 2:63000, 3:630000}
        kml = TEST_make_temp_kml(key_to_range[int(area_id)])

        # generate XML tree into a string buffer
        # TODO: should stream this directly to the client, instead allocation
        # a big memory buffer
        kml_str = etree.tostring(kml)

        # return 
        return HttpResponse(kml_str, mimetype='application/vnd.google-earth.kmz')

class ViewerView(AppView2):
    """
    Renders a simple tree with KML files available in the database.
    The KML viewer browser plugin is controlled directly via JavaScript.
    """

    template_name = 'lizard_kml/viewer.html'

    def get(self, request, kml_type_id=None):
        self.kml_type_id = kml_type_id

        self._kml_type = None
        if self.kml_type_id:
            self._kml_type = KmlType.objects.get(id=int(self.kml_type_id))

        self.url_base = reverse('lizard_kml.viewer', kwargs={'kml_type_id': None})

        return super(ViewerView, self).get(self, request)

    @property
    def kml_type(self):
        return self._kml_type

    def types_tree(self):
        return [
            {
                'name': kml_type.name,
                'url': reverse('lizard_kml.viewer', kwargs={'kml_type_id': kml_type.id}),
                'description': kml_type.description,
            }
            for kml_type in KmlType.objects.all()
        ]

    def areas_tree(self):
        if self.kml_type:
            return [
                {
                    'name': area.name,
                    # disabled: dynamic KML rendering
                    #'kml_url': self.request.build_absolute_uri(reverse('lizard_kml.kml', kwargs={'area_id': area.id})),
                    'kml_url': area.url,
                    'description': area.description
                }
                for area in self.kml_type.area_set.all()
            ]

def TEST_make_querystring_url(**kwargs):
    import urllib
    return reverse('lizard_kml.viewer') + '?' + urllib.urlencode(kwargs)

def TEST_make_temp_kml(range_factor=6300):
    return \
        KML.kml(
            KML.Placemark(
                KML.name("gx:altitudeMode Example"),
                KML.LookAt(
                    KML.longitude(146.806),
                    KML.latitude(12.219),
                    KML.heading(-60),
                    KML.tilt(70),
                    KML.range(range_factor),
                    GX.altitudeMode("relativeToSeaFloor"),
                ),
                KML.LineString(
                    KML.extrude(1),
                    GX.altitudeMode("relativeToSeaFloor"),
                    KML.coordinates(
                      "146.825,12.233,400 "
                      "146.820,12.222,400 "
                      "146.812,12.212,400 "
                      "146.796,12.209,400 "
                      "146.788,12.205,400"
                    )
                )
            )
        )
