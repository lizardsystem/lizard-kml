# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
import mimetypes
from PIL import Image, ImageDraw
import cStringIO
import urllib
import datetime
import traceback

from django.views.generic import TemplateView, View
from django.http import HttpResponse, Http404
from django.core.servers.basehttp import FileWrapper

from lizard_ui.views import ViewContextMixin
from lizard_kml.jarkus.kml import build_kml
from lizard_kml.jarkus.nc_models import makejarkustransect
from lizard_kml.jarkus.plots import (eeg, jarkustimeseries, jarkusmean,
                                     nourishment)

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
    id = None
    url_params = None

    def get(self, request, id=None):
        """
        generate info into a response
        """
        self.id = int(id)

        url_params = {}

        year_from = request.GET.get('year_from', None)
        if year_from:
            url_params['year_from'] = int(year_from)

        year_to = request.GET.get('year_to', None)
        if year_to:
            url_params['year_to'] = int(year_to)

        self.url_params = urllib.urlencode(url_params)

        dt_from = (datetime.datetime(int(year_from), 1, 1) if year_from else
                   None)
        dt_to = (datetime.datetime(int(year_to), 12, 31, 23, 59, 59) if
                 year_to else None)
        self.transect = makejarkustransect(self.id, dt_from, dt_to)

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
        sheet = wb.add_sheet('Transect {0}'.format(self.id))
        for i, row in enumerate(gettable(self.id)):
            for j, value in enumerate(row):
                sheet.write(i, j, value)
        wb.save(stream)
        bytes = stream.getvalue()
        response = HttpResponse(bytes, content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'attachment; filename=transect{0}.xls'.format(self.id)
        return response

class ChartView(View):
    """
    Renders a dynamic Chart image.
    """
    download = False

    def get(self, request, chart_type, id=None, format='png'):
        """generate info into a response"""
        year_from = request.GET.get('year_from')
        year_to = request.GET.get('year_to')
        dt_from = datetime.datetime(int(year_from), 1, 1) if year_from else None
        dt_to = datetime.datetime(int(year_to), 12, 31, 23, 59, 59) if year_to else None

        format = request.GET.get('format', format)
        if not self.download and not format in ['svg', 'png']:
            raise Http404

        id_str = ''
        if id:
            id = int(id)
            id_str = str(id)
        id_min = request.GET.get('id_min') # e.g. 7003001
        id_max = request.GET.get('id_max') # e.g. 7003150
        if id_min and id_max:
            id_min = int(id_min)
            id_max = int(id_max)
            id_str = '{0}-{1}'.format(id_min, id_max)

        # TODO, sanitize the GET.... (pass format=png/pdf, width/height etc?)
        try:
            if chart_type == 'eeg':
                transect = makejarkustransect(id, dt_from, dt_to)
                fd = eeg(transect, {'format': format})
            elif chart_type == 'jarkustimeseries':
                id = int(id)
                transect = makejarkustransect(id, dt_from, dt_to)
                fd = jarkustimeseries(transect, {'format': format})
            elif chart_type == 'nourishment':
                id = int(id)
                fd = nourishment(id, dt_from, dt_to, {'format': format})
            elif chart_type == 'jarkusmean':
                fd = jarkusmean(id_min, id_max, {'format': format})
            else:
                raise Exception('Unknown chart type')
        except Exception as ex:
            logger.exception('exception while rendering chart')
            fd = message_in_png(traceback.format_exc())
        # wrap the file descriptor as a generator (8 KB reads)
        wrapper = FileWrapper(fd)
        if format == 'svg':
            mimetype = 'image/svg+xml'
        else:
            mimetype = mimetypes.types_map['.%s' % format]
        response = HttpResponse(wrapper, content_type=mimetype)
        if self.download:
            response['Content-Disposition'] = 'attachment; filename=transect-{0}-{1}.{2}'.format(id_str, chart_type, format)
        return response

def message_in_png(text):
    '''returns a PNG image generated using PIL'''

    # wrap text so it fits in the image
    #lines = textwrap.wrap(text, width=100, replace_whitespace=False)
    lines = text.split('\n')
    # create image and drawer
    im = Image.new('RGB', (800, 600))
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
