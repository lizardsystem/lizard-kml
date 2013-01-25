# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.template import Context, Template
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.contrib.gis.shortcuts import render_to_kmz, compress_kml
from django.views.decorators.cache import never_cache

from lizard_ui.views import ViewContextMixin
from lizard_kml.models import Category, KmlResource
from lizard_kml.utils import cache_result
from lizard_kml.jarkus.kml import build_kml

from pprint import pprint
import logging
import urllib2
import contextlib
import datetime
import calendar

logger = logging.getLogger(__name__)

KML_MIRROR_CACHE_DURATION = 60 * 60 * 48 # in seconds: 24 hour
KML_MIRROR_FETCH_TIMEOUT = 30 # in seconds
KML_MIRROR_MAX_CONTENT_LENGTH = 1024 * 1024 * 16 # in bytes: 16 MB
MIME_KML = 'application/vnd.google-earth.kml+xml'
MIME_KMZ = 'application/vnd.google-earth.kmz'
KML_MIRROR_TYPES = [MIME_KML, MIME_KMZ]
MIME_TO_EXT = {
    MIME_KML: 'kml',
    MIME_KMZ: 'kmz',
}
COLOR_MAPS = [
    ('GnBu', (0, 0, 200, 21)),
    ('Greys', (0, 25, 200, 46)),
    ('Oranges', (0, 50, 200, 71)),
    ('autumn', (0, 76, 200, 97)),
    ('Blues', (0, 101, 200, 122)),
    ('cool', (0, 126, 200, 147)),
    ('hot', (0, 152, 200, 173)),
    ('hsv', (0, 177, 200, 198)),
    ('summer', (0, 202, 200, 223)),
    ('YlGn', (0, 228, 200, 249)),
    ('bwr', (0, 253, 200, 274)),
    ('YlOrBr', (0, 278, 200, 300))
]

class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"

def urlopen(request):
    return contextlib.closing(urllib2.urlopen(request, timeout=KML_MIRROR_FETCH_TIMEOUT))

@cache_result(KML_MIRROR_CACHE_DURATION, ignore_cache=False)
def get_mirrored_kml(url):
    logger.info("Downloading %s.", url)
    with urlopen(urllib2.Request(url)) as response:
        headers = response.info()
        last_modified = headers.getdate('Last-Modified')

        # check the content type
        content_type = headers['Content-Type'].strip()

        # sometimes servers like to add ';mode=networklink' to the content-type
        if ';' in content_type:
            content_type = content_type.split(';')[0]

        # ensure only known types are proxy'd
        if content_type not in KML_MIRROR_TYPES:
            raise Exception('Unsupported Content-Type')

        # prevent humongous downloads
        # some servers (Geoserver...) won't even send this header
        if 'Content-Length' in headers:
            content_length = int(headers['Content-Length'].strip())
            if content_length >= KML_MIRROR_MAX_CONTENT_LENGTH:
                raise Exception('KML_MIRROR_MAX_CONTENT_LENGTH exceeded')

        # perform the download
        content = response.read(KML_MIRROR_MAX_CONTENT_LENGTH)

        # when len(content) == KML_MIRROR_MAX_CONTENT_LENGTH,
        # this probably means there's more data available
        if len(content) >= KML_MIRROR_MAX_CONTENT_LENGTH:
            raise Exception('KML_MIRROR_MAX_CONTENT_LENGTH exceeded')

        # recompress KML to KMZ
        if content_type == MIME_KML:
            logger.info("Compressing %s to KMZ.", url)
            content = compress_kml(content)
            content_type = MIME_KMZ
        return content, content_type

def get_wms_kml(kml_resource):
    context = {
        'name': kml_resource.name,
        'wms_url': kml_resource.url
    }
    content = render_to_kmz("kml/wms.kml", context)
    content_type = MIME_KMZ
    return content, content_type

class KmlResourceView(View):
    @method_decorator(never_cache)
    def get(self, request, kml_resource_id):
        kml_resource = get_object_or_404(KmlResource, pk=kml_resource_id)
        logger.debug('Serving KML %s', kml_resource)
        if kml_resource.kml_type == 'static':
            content, content_type = get_mirrored_kml(kml_resource.url)
        elif kml_resource.kml_type == 'wms':
            content, content_type = get_wms_kml(kml_resource)
        else:
            raise Exception('KML is dynamic, please use its specific URL as found in urls.py.')
        response = HttpResponse(content, content_type=content_type)
        # properly add extension, all though it's mostly ignored
        ext = MIME_TO_EXT.get(content_type, 'kml')
        response['Content-Disposition'] = 'attachment; filename=kml_resource{}.{}'.format(kml_resource.pk, ext)
        return response

class ViewerView(ViewContextMixin, TemplateView):
    """
    Renders a simple tree with KML files available in the database.
    The KML viewer browser plugin is controlled directly via JavaScript.
    """

    template_name = 'lizard_kml/viewer.html'

    def get(self, request):
        return super(ViewerView, self).get(self, request)

    def color_maps(self):
        return COLOR_MAPS
