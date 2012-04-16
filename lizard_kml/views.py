# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.conf import settings

from lizard_ui.views import ViewContextMixin
from lizard_kml.kml import build_kml, build_test_kml

import logging


logger = logging.getLogger(__name__)


class KmlView(View):
    """
    Renders a dynamic KML file.
    """

    def get(self, request, kml_type, id=None):
        """generate KML XML tree into a zipfile response"""

        try:
            args = {}
            args.update(request.GET.items())
            if id is not None:
                args['id'] = int(id)
            return build_kml(self, kml_type, args)
        except:
            if settings.DEBUG_SHOW_EXAMPLE_KML_ON_EXCEPTION:
                logger.exception('error building kml')
                return build_test_kml()
            else:
                raise


class ViewerView(ViewContextMixin, TemplateView):
    """
    Renders a simple tree with KML files available in the database.
    The KML viewer browser plugin is controlled directly via JavaScript.
    """

    template_name = 'lizard_kml/viewer.html'

    def get(self, request, kml_type_id=None):
        #disabled: don't support zooming to specific areas yet
        #self.kml_type_id = kml_type_id
        #
        #if self.kml_type_id:
        #    self._kml_type = KmlType.objects.get(id=int(self.kml_type_id))
        #else:
        #    self._kml_type = None

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
