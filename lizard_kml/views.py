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
from lizard_kml.nc_models import makejarkustransect
from lizard_kml.profiling import profile
from lizard_kml.plots import eeg, jarkustimeseries
import logging
import xlwt

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

class InfoView(ViewContextMixin, TemplateView):
    """
    Renders a dynamic KML file.
    """
    template_name = "lizard_kml/info.html"
    #@profile('kml.pyprof')
    def get(self, request, id=None):
        """generate info into a response"""

        self.id = int(id)
        return super(InfoView, self).get(self, request)
    def gettable(self):
        return gettable(self.id)
def gettable(id):
    tr = makejarkustransect(id)
    return zip(tr.x, tr.y, tr.cross_shore, tr.z[-1])
class XlsView(View):
    """
    Renders a dynamic XLS file.
    """

    #@profile('kml.pyprof')
    def get(self, request, id=None):
        """generate info into a response"""

        self.id = int(id)
        import cStringIO
        import xlwt
        stream = cStringIO.StringIO()
        wb = xlwt.Workbook()
        sheet = wb.add_sheet('Transect {}'.format(self.id))
        for i, row in enumerate(gettable(self.id)):
            for j, value in enumerate(row):
                sheet.write(i,j,value)
        wb.save(stream)
        bytes = stream.getvalue()
        response = HttpResponse(bytes, mimetype="application/vnd.ms-excel")
        response['Content-Disposition'] = 'attachment; filename=transect{}.xls'.format(self.id)
        return response


class ChartView(View):
    """
    Renders a dynamic Chart file.
    """

    def get(self, request, chart_type, id=None):
        """generate info into a response"""

        self.id = int(id)
        import cStringIO
        transect = makejarkustransect(id)
        # TODO, sanitize the GET.... (format=png/pdf,size?)
        if chart_type == 'eeg':
            bytes = eeg(transect, {'format':'png'})
        elif chart_type == 'jarkustimeseries':
            bytes = jarkustimeseries(transect, {'format':'png' })
        response = HttpResponse(bytes, mimetype="image/png")
        # TODO for pdf:
        # response['Content-Disposition'] = 'attachment; filename=transect{}.{}'.format(self.id, format=format)
        return response

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
                    'is_dynamic': kml_resource.is_dynamic,
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

    def color_maps(self):
        return COLOR_MAPS

COLOR_MAPS = [
    ('Accent', (0, 1)),
    ('Blues', (262, 1)),
    ('BrBG', (0, 8)),
    ('BuGn', (262, 8)),
    ('BuPu', (0, 15)),
    ('Dark2', (262, 15)),
    ('GnBu', (0, 22)),
    ('Greens', (262, 22)),
    ('Greys', (0, 29)),
    ('OrRd', (262, 29)),
    ('Oranges', (0, 36)),
    ('PRGn', (262, 36)),
    ('Paired', (0, 43)),
    ('Pastel1', (262, 43)),
    ('Pastel2', (0, 50)),
    ('PiYG', (262, 50)),
    ('PuBu', (0, 57)),
    ('PuBuGn', (262, 57)),
    ('PuOr', (0, 64)),
    ('PuRd', (262, 64)),
    ('Purples', (0, 71)),
    ('RdBu', (262, 71)),
    ('RdGy', (0, 78)),
    ('RdPu', (262, 78)),
    ('RdYlBu', (0, 85)),
    ('RdYlGn', (262, 85)),
    ('Reds', (0, 92)),
    ('Set1', (262, 92)),
    ('Set2', (0, 99)),
    ('Set3', (262, 99)),
    ('Spectral', (0, 106)),
    ('YlGn', (262, 106)),
    ('YlGnBu', (0, 113)),
    ('YlOrBr', (262, 113)),
    ('YlOrRd', (0, 120)),
    ('afmhot', (262, 120)),
    ('autumn', (0, 127)),
    ('binary', (262, 127)),
    ('bone', (0, 133)),
    ('brg', (262, 133)),
    ('bwr', (0, 140)),
    ('cool', (262, 140)),
    ('coolwarm', (0, 147)),
    ('copper', (262, 147)),
    ('cubehelix', (0, 154)),
    ('flag', (262, 154)),
    ('gist_earth', (0, 161)),
    ('gist_gray', (262, 161)),
    ('gist_heat', (0, 168)),
    ('gist_ncar', (262, 168)),
    ('gist_rainbow', (0, 175)),
    ('gist_stern', (262, 175)),
    ('gist_yarg', (0, 182)),
    ('gnuplot', (262, 182)),
    ('gnuplot2', (0, 189)),
    ('gray', (262, 189)),
    ('hot', (0, 196)),
    ('hsv', (262, 196)),
    ('jet', (0, 203)),
    ('ocean', (262, 203)),
    ('pink', (0, 210)),
    ('prism', (262, 210)),
    ('rainbow', (0, 217)),
    ('seismic', (262, 217)),
    ('spectral', (0, 224)),
    ('spring', (262, 224)),
    ('summer', (0, 231)),
    ('terrain', (262, 231)),
    ('winter', (0, 238))
]

COLOR_MAPS = [(name, '%i,%i,%i,%i' % (x, y, x + 218, y + 5)) for name, (x, y) in COLOR_MAPS]
