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

    def get(self, request, id=None):
        """
        generate info into a response
        """
        self.id = int(id)

        year_from = request.GET.get('year_from', None)
        year_to = request.GET.get('year_to', None)

        dt_from = (datetime.datetime(int(year_from), 1, 1) if year_from else
                   None)
        dt_to = (datetime.datetime(int(year_to), 12, 31, 23, 59, 59) if
                 year_to else None)
        self.transect = makejarkustransect(self.id, dt_from, dt_to)

        return super(InfoView, self).get(self, request)

    def gettable(self):
        return gettable(self.id)

class JarkusmeanInfoView(ViewContextMixin, TemplateView):
    template_name = "jarkus/info_jarkusmean.html"

    def get(self, request):
        self.id_min = request.GET.get('id_min')
        self.id_max = request.GET.get('id_max')
        return super(JarkusmeanInfoView, self).get(self, request)

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
        year_from = request.GET.get('year_from')
        year_to = request.GET.get('year_to')
        width = request.GET.get('width')
        height = request.GET.get('height')
        dt_from = datetime.datetime(int(year_from), 1, 1) if year_from else None
        dt_to = datetime.datetime(int(year_to), 12, 31, 23, 59, 59) if year_to else None

        # When set, override the format with the passed GET parameter 'format'.
        format = request.GET.get('format', format)
        if format not in ['svg', 'png', 'pdf']:
            raise Http404

        # Sanitize transect IDs by converting them to ints.
        if id:
            id = int(id)
        id_min = request.GET.get('id_min') # e.g. 7003001
        id_max = request.GET.get('id_max') # e.g. 7003150
        if id_min and id_max:
            id_min = int(id_min)
            id_max = int(id_max)

        try:
            dpi = 100 # matplotlib default DPI
            plotproperties = {
                'format': format,
                'dpi': dpi
            }
            if width and height:
                figsize = (float(width) / dpi, float(height) / dpi)
            else:
                figsize = None

            # Determine what function to use to render the chart.
            if chart_type == 'eeg':
                transect = makejarkustransect(id, dt_from, dt_to)
                fd = eeg(transect, plotproperties, figsize)
            elif chart_type == 'jarkustimeseries':
                transect = makejarkustransect(id, dt_from, dt_to)
                fd = jarkustimeseries(transect, plotproperties, figsize)
            elif chart_type == 'nourishment':
                fd = nourishment(id, dt_from, dt_to, plotproperties, figsize)
            elif chart_type == 'jarkusmean':
                fd = jarkusmean(id_min, id_max, plotproperties, figsize)
            else:
                raise Exception('Unknown chart type')
        except Exception as ex:
            logger.exception('exception while rendering chart')
            fd = message_in_png(traceback.format_exc())
            format = 'png'

        # Wrap the file descriptor as a generator (8 KB reads).
        wrapper = FileWrapper(fd)

        # Determine correct mimetype.
        if format == 'svg':
            mimetype = 'image/svg+xml'
        else:
            mimetype = mimetypes.types_map['.%s' % format]

        # Build a response which streams the wrapped buffer.
        response = HttpResponse(wrapper, content_type=mimetype)

        # Add a header containing the filename, so the browser knows how to call the saved file.
        if self.download:
            if id_min and id_max:
                id_str = '{0}-{1}'.format(id_min, id_max)
            elif id:
                id_str = str(id)
            else:
                id_str = ''
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
