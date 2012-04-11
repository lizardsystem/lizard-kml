# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.contrib.gis.shortcuts import render_to_kmz, compress_kml

from pykml.factory import KML_ElementMaker as KML
from pykml.factory import GX_ElementMaker as GX
from lxml import etree

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
