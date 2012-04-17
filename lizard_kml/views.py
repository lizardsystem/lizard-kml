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
from lizard_kml.models import Category, KmlResource
from lizard_kml.kml import build_kml
from lizard_kml.profiling import profile

import logging


logger = logging.getLogger(__name__)


class KmlView(View):
    """
    Renders a dynamic KML file.
    """

    #@profile('kml.pyprof')
    def get(self, request, kml_type, id=None):
        """generate KML XML tree into a zipfile response"""

        args = {}
        args.update(request.GET.items())
        if id is not None:
            args['id'] = int(id)
        return build_kml(self, kml_type, args)


class ViewerView(ViewContextMixin, TemplateView):
    """
    Renders a simple tree with KML files available in the database.
    The KML viewer browser plugin is controlled directly via JavaScript.
    """

    template_name = 'lizard_kml/viewer.html'

    def get(self, request, category_id=None):
        self.category_id = category_id

        if self.category_id:
            self._category = Category.objects.get(id=int(self.category_id))
        else:
            self._category = None

        return super(ViewerView, self).get(self, request)

    @property
    def category(self):
        return self._category

    def category_tree(self):
        return [
            {
                'name': category.name,
                'url': reverse('lizard-kml-viewer', kwargs={'category_id': category.id}),
                'description': category.description,
            }
            for category in Category.objects.all()
        ]

    def kml_resource_tree(self):
        if self.category:
            return [
                {
                    'name': kml_resource.name,
                    'kml_url': self._mk_kml_resource_url(kml_resource),
                    #'kml_url': area.url,
                    'description': kml_resource.description,
                }
                for kml_resource in self.category.kmlresource_set.all()
            ]

    def _mk_kml_resource_url(self, kml_resource):
        if kml_resource.is_dynamic:
            return self.request.build_absolute_uri(
                reverse('lizard-kml-kml', kwargs={'kml_type': kml_resource.kml_type}))
        else:
            return kml_resource.url
