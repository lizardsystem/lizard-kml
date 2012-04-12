# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
import os

from django.template.loader import render_to_string
from django.contrib.gis.shortcuts import render_to_kmz, compress_kml

from nc_models import makejarkustransect, makejarkusoverview


# creates a dict of factory functions
factories = {
    # assume transectid as extra argument
    'transect': makejarkustransect,
    # assume transectid as extra argument
    'overview': makejarkusoverview,
    # Just a dict with the extra options.
    'lod': dict
}

def build_kml(kml_type, kml_args_dict):
    '''builds a dynamic KML file'''
    factory_meth = factories[kml_type]
    # n.b.: kml_args_dict containts direct USER input
    # This means that we should process input as unsafe in the factory methods...
    # Do that here (only get the id, convert it to int)
    if 'id' in kml_args_dict:
        template_context = factory_meth(id=int(kml_args_dict['id']))
    else:
        template_context = factory_meth()
    return render_to_kmz("kml/{}.kml".format(kml_type), template_context)

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
