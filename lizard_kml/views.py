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
    @never_cache
    def get(self, request, kml_resource_id):
        kml_resource = get_object_or_404(KmlResource, pk=kml_resource_id)
        if not kml_resource.is_dynamic:
            content, content_type = get_mirrored_kml(kml_resource.url)
        else:
            # TODO HACK REMOVE ME
            args = {}
            args.update(request.GET.items())
            content = build_kml(self, 'lod', args)
            content_type = MIME_KMZ
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


COLOR_MAPS = [('GnBu', (0, 0, 200, 21)),
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
 ('YlOrBr', (0, 278, 200, 300))]
