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
from django.contrib.gis.shortcuts import render_to_kmz, compress_kml

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

KML_MIRROR_CACHE_DURATION = 60 * 60 * 24 # in seconds: 24 hour
KML_MIRROR_FETCH_TIMEOUT = 30 # in seconds
KML_MIRROR_MAX_CONTENT_LENGTH = 1024 * 1024 * 16 # in bytes: 16 MB
MIME_KML = 'application/vnd.google-earth.kml+xml'
MIME_KMZ = 'application/vnd.google-earth.kmz'
KML_MIRROR_TYPES = [MIME_KML, MIME_KMZ]

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
        if content_type not in KML_MIRROR_TYPES:
            raise Exception('Unsupported Content-Type')

        # prevent humongous downloads
        content_length = int(headers['Content-Length'].strip())
        if content_length >= KML_MIRROR_MAX_CONTENT_LENGTH:
            raise Exception('KML_MIRROR_MAX_CONTENT_LENGTH exceeded')

        # perform the download
        content = response.read(KML_MIRROR_MAX_CONTENT_LENGTH)

        # recompress KML to KMZ
        if content_type == MIME_KML:
            logger.info("Compressing %s to KMZ.", url)
            content = compress_kml(content)
            content_type = MIME_KMZ
        return content, content_type

class KmlResourceView(View):
    def get(self, request, kml_resource_id):
        kml_resource = get_object_or_404(KmlResource, pk=kml_resource_id)
        if not kml_resource.is_dynamic:
            content, content_type = get_mirrored_kml(kml_resource.url)
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = 'attachment; filename=kml_resource{}.kmz'.format(kml_resource.pk)
        return response

class ViewerView(ViewContextMixin, TemplateView):
    """
    Renders a simple tree with KML files available in the database.
    The KML viewer browser plugin is controlled directly via JavaScript.
    """

    template_name = 'lizard_kml/viewer.html'

    def get(self, request):
        return super(ViewerView, self).get(self, request)

    def category_tree(self):
        try:
            return [
                {
                    'name': category.name,
                    'description': category.description,
                    'children': self._kml_resource_tree(category),
                }
                for category in Category.objects.all()
            ]
        except Exception as ex:
            # wrap exception here to ensure
            # exception doesn't have silent_variable_failure set
            raise Exception(ex)

    def _kml_resource_tree(self, category):
        return [
            {
                'id': kml_resource.pk,
                'name': kml_resource.name,
                'url': self._mk_kml_resource_url(kml_resource),
                'is_dynamic': kml_resource.is_dynamic,
                'description': kml_resource.description,
                'preview_image_url': kml_resource.preview_image.url
            }
            for kml_resource in category.kmlresource_set.all()
        ]

    def _mk_kml_resource_url(self, kml_resource):
        if kml_resource.is_dynamic:
            rela = reverse('lizard-jarkus-kml', kwargs={'kml_type': 'lod'})
        else:
            rela = reverse('lizard-kml-kml', kwargs={'kml_resource_id': kml_resource.pk})
        now = calendar.timegm(datetime.datetime.utcnow().utctimetuple())
        return self.request.build_absolute_uri(rela) + '?timestamp=' + str(now)

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
