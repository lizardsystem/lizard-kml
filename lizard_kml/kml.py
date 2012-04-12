# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
import os

from django.template.loader import render_to_string
from django.contrib.gis.shortcuts import render_to_kmz, compress_kml


from netCDF4 import Dataset

import random; random.seed()

NC_RESOURCE = 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/jarkus/profiles/transect.nc'
# optional, download local: wget http://opendap.deltares.nl/thredds/fileServer/opendap/rijkswaterstaat/jarkus/profiles/transect.nc

#@cached(expiry=60) # TODO

from models import makejarkustransect, makejarkusoverview

# creates a dict of factory functions that correspond to views
factories = {'transect': makejarkustransect,
             'overview': makejarkusoverview}
def build_kml(template_name, **kwargs):
    '''builds a dynamic KML file'''

    if template_name == 'transect':
        # assume transectid as extra argument
        transect = makejarkustransect(kwargs['transectid'])
    elif template_name == 'overview':
        # assume transectid as extra argument
        overview = makejarkusoverview()
    return render_to_kmz("kml/{}.kml".format(template_name), locals())

