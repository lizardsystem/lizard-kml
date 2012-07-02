# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.conf import settings
from django.utils.translation import ugettext as _

from lizard_ui.views import ViewContextMixin
from lizard_kml.jarkus.kml import build_kml
from lizard_kml.jarkus.nc_models import makejarkustransect
from lizard_kml.jarkus.plots import eeg, jarkustimeseries

import logging
import xlwt

logger = logging.getLogger(__name__)

class JarkusKmlView(View):
    """
    Renders a dynamic KML file.
    """

    def get(self, request, kml_type, id=None):
        """generate KML XML tree into a zipfile response"""

        kml_args_dict = {}
        kml_args_dict.update(request.GET.items())
        if id is not None:
            id = int(id)
        return build_kml(self, kml_type, id, kml_args_dict)

class InfoView(ViewContextMixin, TemplateView):
    """
    Renders a dynamic KML file.
    """
    template_name = "lizard_kml/info.html"

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
