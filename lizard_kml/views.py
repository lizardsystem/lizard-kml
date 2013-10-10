# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.template import Context, Template
from django.shortcuts import render_to_response, get_object_or_404
from django.template.loader import render_to_string
from django.utils import simplejson as json
from django.views.generic import TemplateView, View
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.conf import settings
from django.utils.translation import ugettext
from django.utils.decorators import method_decorator
from django.contrib.gis.shortcuts import render_to_kmz, compress_kml
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

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

# Constants related to mirroring KML files.
KML_MIRROR_FETCH_TIMEOUT = 10 # in seconds
KML_MIRROR_MAX_CONTENT_LENGTH = 1024 * 1024 * 16 # in bytes: 16 MB
MIME_KML = 'application/vnd.google-earth.kml+xml'
MIME_KMZ = 'application/vnd.google-earth.kmz'
KML_MIRROR_TYPES = [MIME_KML, MIME_KMZ]
MIME_TO_EXT = {
    MIME_KML: 'kml',
    MIME_KMZ: 'kmz',
}

# Maps the name of the colormap to the pixel area in the generated color_maps.png.
# Use the management command "gen_colormaps" for this.
# The HTML containing <area> tags is generated in the viewer.html template.
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

class ViewContextMixin(object):
    """View mixin that adds the view object to the context.

    Make sure this is near the front of the inheritance list: it should come
    before other mixins that (re-)define ``get_context_data()``.

    When you use this mixin in your view, you can do ``{{ view.some_method
    }}`` or ``{{ view.some_attribute }}`` in your class and it will call those
    methods or attributes on your view object: no more need to pass in
    anything in a context dictionary, just stick it on ``self``!

    """
    def get_context_data(self, **kwargs):
        """Return context with view object available as 'view'."""
        try:
            context = super(ViewContextMixin, self).get_context_data(**kwargs)
        except AttributeError:
            context = {}
        context.update({'view': self})
        return context

class LoginRequiredMixin(object):
    """Ensures that user must be authenticated in order to access view."""

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)

class HeadRequest(urllib2.Request):
    '''
    Add missing HTTP HEAD request to urllib.
    '''
    def get_method(self):
        return "HEAD"

def urlopen(request):
    '''
    Shorthand which returns a context-managed urlopen for use with the new "with" statement.
    '''
    return contextlib.closing(urllib2.urlopen(request, timeout=KML_MIRROR_FETCH_TIMEOUT))

def get_mirrored_kml(url):
    '''
    Mirror external data located at given url, so it can be served with our
    own webserver. The downloaded data is cached for 24 hours.

    Returns a tuple (content, content_type).
    '''
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
    '''
    Wrap a WMS url in a KML file for given KmlResource instance.

    Returns a tuple (content, content_type).
    '''
    context = {
        'name': kml_resource.name,
        'wms_url': kml_resource.url
    }

    # Build KML file using a simple Django template.
    content = render_to_kmz("kml/wms.kml", context)
    content_type = MIME_KMZ
    return content, content_type

class KmlResourceView(View):
    '''
    View which returns the KML file related to passed kml_resource_id.
    '''
    @method_decorator(never_cache)
    def get(self, request, kml_resource_id, ext=None):
        kml_resource = get_object_or_404(KmlResource, pk=kml_resource_id)
        logger.debug('Serving KML %s', kml_resource)

        # Determine what to serve.
        if kml_resource.kml_type == 'static':
            content, content_type = get_mirrored_kml(kml_resource.url)
        elif kml_resource.kml_type == 'wms':
            content, content_type = get_wms_kml(kml_resource)
        else:
            raise Exception('KML is dynamic, please use its specific URL as found in urls.py.')

        # Wrap the file a in HTTP response.
        response = HttpResponse(content, content_type=content_type)

        # Properly add extension and filename, even though it's mostly ignored.
        ext = MIME_TO_EXT.get(content_type, 'kml')
        response['Content-Disposition'] = 'attachment; filename=kml_resource{0}.{1}'.format(kml_resource.pk, ext)

        return response

class ViewerView(ViewContextMixin, TemplateView):
    '''
    Returns the main HTML for lizard-kml.
    Renders a simple tree with KML files available in the database.
    The KML viewer browser plugin is controlled directly via JavaScript.
    '''
    template_name = 'lizard_kml/viewer.html'

    def color_maps(self):
        return COLOR_MAPS
