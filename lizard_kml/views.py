# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from django.middleware.gzip import GZipMiddleware
from django.contrib.gis.shortcuts import render_to_kmz
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from lizard_ui.views import ViewContextMixin

from lizard_kml.models import makejarkustransect, makejarkusoverview,  KmlType

from lizard_kml.kml import build_kml
import lizard_kml.helpers as h
gzip_middleware = GZipMiddleware()

class KmlView(View):
    """
    Renders a dynamic KML file.
    """

    def get(self, request, **kwargs):
        """generate KML XML tree into a zipfile response"""
        # TODO: should stream this directly to the client, instead allocating
        # If the result needs to be streamed it can't be a kmz
        # because kmz is a zipfile that contains a file doc.kml
        # a big memory buffer
        # The least memory consumption would probably be something like:
        # zf.writestr("doc.kml", stringio.getvalue())
        # you have to replace the render_to_kmz as that only supports strings.
        template_name = 'transect'
        if template_name == 'transect':
            # assume transectid as extra argument
            transect = makejarkustransect(id=int(kwargs['id']))
        elif template_name == 'overview':
            # assume transectid as extra argument
            overview = makejarkusoverview()
        
        response = render_to_kmz(
            "kml/{}.kml".format(template_name),
            locals()
            )
        return response


class ViewerView(ViewContextMixin, TemplateView):
    """
    Renders a simple tree with KML files available in the database.
    The KML viewer browser plugin is controlled directly via JavaScript.
    """

    template_name = 'lizard_kml/viewer.html'

    def get(self, request, kml_type_id=None):
        self.kml_type_id = kml_type_id

        if self.kml_type_id:
            self._kml_type = KmlType.objects.get(id=int(self.kml_type_id))
        else:
            self._kml_type = None

        return super(ViewerView, self).get(self, request)

    @property
    def kml_type(self):
        return self._kml_type

    def types_tree(self):
        return [
            {
                'name': kml_type.name,
                'url': reverse('lizard-kml-viewer', kwargs={'kml_type_id': kml_type.id}),
                'description': kml_type.description,
            }
            for kml_type in KmlType.objects.all()
        ]

    def areas_tree(self):
        if self.kml_type:
            return [
                {
                    'name': area.name,
                    'kml_url': self.request.build_absolute_uri(reverse('lizard-kml-kml', kwargs={'id': area.id})),
                    #'kml_url': area.url,
                    'description': area.description,
                }
                for area in self.kml_type.area_set.all()
            ]
