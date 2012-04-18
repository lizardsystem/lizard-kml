# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
import os
import collections

from django.template.loader import render_to_string
from django.contrib.gis.shortcuts import render_to_kmz, compress_kml

from nc_models import makejarkustransect, makejarkusoverview
from lizard_kml import helpers
import numpy as np
import matplotlib.cm
import matplotlib.colors
import logging
logger = logging.getLogger(__name__)


def build_kml(view, kml_type, kml_args_dict):
    '''builds a dynamic KML file'''
    # n.b.: kml_args_dict containts direct USER input
    # This means that we should process input as unsafe in the factory methods...
    template_context = {'view': view}
    if kml_type == 'transect':
        id = int(kml_args_dict['id'])
        transect = makejarkustransect(id)
        extra_context = build_transect_context(transect, kml_args_dict)
        template_context.update(extra_context)
    if kml_type == 'lod':
        overview = makejarkusoverview()
        extra_context = build_overview_context(overview, kml_args_dict)
        template_context.update(extra_context)
    return render_to_kmz("kml/{}.kml".format(kml_type), template_context)

def build_overview_context(overview, kml_args_dict):
    """
    Return the formatted overview as input for the kml
    >>> overview = makejarkusoverview()
    >>> build_overview_context(overview, {}) # doctest:+ELLIPSIS
    {'overview':..., 'lines': [{'bbox': {'...': ...}, 'coordinates':...
    """
    result = {}
    result['overview'] = overview
    lines = []
    for (id,
         north,
         south,
         east,
         west,
         lat0,
         lat1,
         lon0,
         lon1) in zip(overview['id'],
                      overview['north'],
                      overview['south'],
                      overview['east'],
                      overview['west'],
                      overview['lat0'],
                      overview['lat1'],
                      overview['lon0'],
                      overview['lon1']):
        line = {}
        bbox = {
            'north': north,
            'south': south,
            'east': east,
            'west': west
            }
        coordinates = helpers.textcoordinates(x0=lon0, y0=lat0, x1=lon1, y1=lat1)
        line['coordinates'] = coordinates
        line['bbox'] = bbox
        line['id'] = id
        lines.append(line)
    result['lines'] = lines
    result['exaggeration'] = float(kml_args_dict.get('exaggeration', 4))
    result['lift'] = float(kml_args_dict.get('lift', 40))
    
    return result


def build_transect_context(transect, kml_args_dict):
    """
    Return a formatted transect object as input for the kml
    >>> transect = makejarkustransect(7003800)
    >>> build_transect_context(transect, {}) # doctest:+ELLIPSIS
    {...'transect': <lizard_kml...>,...'years': OrderedDict([(datetime...
    """
    result = {}
    result['transect'] = transect
    years = collections.OrderedDict()
    exaggeration = float(kml_args_dict.get('exaggeration', 4))
    lift = float(kml_args_dict.get('lift', 40))
    for i, year in enumerate(transect.t):
        coords = helpers.textcoordinates(
            transect.lon,
            transect.lat,
            transect.z[i,:] * exaggeration + lift
            )
        years[year] = {
            'coordinates': coords,
            'begindate': helpers.kmldate(transect.begindates()[i]),
            'enddate': helpers.kmldate(transect.enddates()[i]),
            'style': 'year{}'.format(transect.begindates()[i].year)
            }
    result['years'] = years
    # not quite accurate, fix datetime problem first.. 1970!=1970
    # Get a colormap based on the ?colormap parameter
    colormap = matplotlib.cm.cmap_d.get(kml_args_dict.get('colormap', 'YlGn_r'), matplotlib.cm.YlGn_r)
    
    colors = {}
    # HACK: This can be done a bit nicer and the styles can be references to an external file (through styleurl)
    for year in range(1964, 2015):
        # call with float 0..1 (or int 0 .. 255)
        r,g,b, alpha = colormap(float(year-1964)/float(2015-1964))
        color = matplotlib.colors.rgb2hex((b, g, r)).replace('#', '') # r and b reversed in the google, don't forget to add alpha
        colors['year{}'.format(year)] = color
    result['colors'] = colors
    return result

def build_test_kml():
    '''build a simple KML file with a simple LineString, for testing purposes'''

    from pykml.factory import KML_ElementMaker as KML
    from pykml.factory import GX_ElementMaker as GX
    from lxml import etree
    from django.http import HttpResponse

    kml = KML.kml(
        KML.Placemark(
            KML.name("build_test_kml output"),
            KML.LookAt(
                KML.longitude(146.806),
                KML.latitude(12.219),
                KML.heading(-60),
                KML.tilt(70),
                KML.range(6300),
                GX.altitudeMode("relativeToSeaFloor"),
            ),
            KML.LineString(
                KML.extrude(1),
                GX.altitudeMode("relativeToSeaFloor"),
                KML.coordinates(
                    "146.825,12.233,400 "
                    "146.820,12.222,400 "
                    "146.812,12.212,400 "
                    "146.796,12.209,400 "
                    "146.788,12.205,400"
                )
            )
        )
    )
    kml_str = etree.tostring(kml)
    return HttpResponse(kml_str, mimetype='application/vnd.google-earth.kml')
