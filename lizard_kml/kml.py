# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.template.loader import render_to_string
from django.contrib.gis.shortcuts import render_to_kmz, compress_kml

from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
from lxml import etree

#import netCDF

import random; random.seed()

#@cached(expiry=60) # TODO
def build_kml(template_name, area_id):
    '''builds a dynamic KML file'''

    # query the db
    # foo = netCDF.load("jarkusdata.bin")
    # matrix = foo.query(a=3)

    # 'calculate' range based on input
    if area_id == 3 or random.choice([True, False]):
        look_at_range = 6300 + 1000 - 500 - 500
    else:
        look_at_range = 4000 + 2000 - 2000

    # do something else
    show_some_example_shape = random.choice([True, False])

    return render_to_string("kml/{}.kml".format(template_name), locals())

def build_test_kml():
    '''build a simple KML file with a simple LineString, for testing purposes'''
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
    return kml_str
