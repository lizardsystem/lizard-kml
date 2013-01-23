# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.servers.basehttp import FileWrapper
from django.conf import settings

from PIL import Image, ImageDraw
import cStringIO
import textwrap

from lizard_ui.views import ViewContextMixin
from lizard_kml.jarkus.kml import build_kml
from lizard_kml.jarkus.nc_models import (
    makejarkustransect,
    NoDataForTransect
)
from lizard_kml.jarkus.plots import (
    eeg,
    jarkustimeseries,
    jarkusmean,
    nourishment,
    WouldTakeTooLong
)

import logging
import xlwt

logger = logging.getLogger(__name__)

class JarkusKmlView(View):
    """
    Renders a jarkus KML file containing either the overview or the
    specific transects.
    """

    def get(self, request, kml_type, id=None):
        """generate KML XML tree into a zipfile response"""

        kml_args_dict = {}
        kml_args_dict.update(request.GET.items())
        if id is not None:
            id = int(id)
        return build_kml(self, kml_type, id, kml_args_dict)

def gettable(id):
    tr = makejarkustransect(id)
    return zip(tr.x, tr.y, tr.cross_shore, tr.z[-1])

class InfoView(ViewContextMixin, TemplateView):
    """
    Renders a html containing charts about a certain transect.
    """
    template_name = "jarkus/info.html"

    def get(self, request, id=None):
        """generate info into a response"""

        self.id = int(id)
        return super(InfoView, self).get(self, request)

    def gettable(self):
        return gettable(self.id)

class XlsView(View):
    """
    Renders transect info about a transect in an Excel .xls file.
    """

    def get(self, request, id=None):
        """generate info into a response"""

        self.id = int(id)
        stream = cStringIO.StringIO()
        wb = xlwt.Workbook()
        sheet = wb.add_sheet('Transect {}'.format(self.id))
        for i, row in enumerate(gettable(self.id)):
            for j, value in enumerate(row):
                sheet.write(i, j, value)
        wb.save(stream)
        bytes = stream.getvalue()
        response = HttpResponse(bytes, content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'attachment; filename=transect{}.xls'.format(self.id)
        return response

class ChartView(View):
    """
    Renders a dynamic Chart image.
    """

    def get(self, request, chart_type, id=None):
        """generate info into a response"""

        # TODO, sanitize the GET.... (pass format=png/pdf, width/height etc?)
        try:
            if chart_type == 'eeg':
                id = int(id)
                transect = makejarkustransect(id)
                fd = eeg(transect, {'format':'png'})
            elif chart_type == 'jarkustimeseries':
                id = int(id)
                transect = makejarkustransect(id)
                fd = jarkustimeseries(transect, {'format':'png'})
            elif chart_type == 'nourishment':
                id = int(id)
                try:
                    fd = nourishment(id, {'format':'png'})
                except NoDataForTransect as ndft:
                    # use the closest transect which does have data
                    # instead
                    id = int(ndft.closest_transect_id)
                    fd = nourishment(id, {'format':'png'})
            elif chart_type == 'jarkusmean':
                id_min = int(request.GET['id_min']) # e.g. 7003001
                id_max = int(request.GET['id_max']) # e.g. 7003150
                fd = jarkusmean(id_min, id_max, {'format':'png'})
        except Exception as ex:
            fd = message_in_png(str(ex))
        # wrap the file descriptor as a generator (8 KB reads)
        wrapper = FileWrapper(fd)
        response = HttpResponse(wrapper, content_type="image/png")
        # TODO for pdf:
        # response['Content-Disposition'] = 'attachment; filename=transect{}.{}'.format(self.id, format=format)
        return response

def message_in_png(text):
    '''returns a PNG image generated using PIL'''

    # wrap text so it fits in the image
    lines = textwrap.wrap(text, width=60)
    # create image and drawer
    im = Image.new('RGB', (400, 300))
    draw = ImageDraw.Draw(im)
    # top-left position
    x0 = 10
    y0 = 10
    # perform the draw
    for i, line in enumerate(lines):
        draw.text((x0, y0 + 12 * i), line, fill=(255, 0, 0))
    # save as a PNG to the provided file-like object
    buf = cStringIO.StringIO()
    im.save(buf, 'PNG')
    buf.seek(0)
    # return an 'open' file descriptor
    return buf
