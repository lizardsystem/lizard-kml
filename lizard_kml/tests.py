# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.test.client import Client
import nose.tools as nt
from django.test import TestCase
from lizard_kml.nc_models import Transect, makejarkustransect
import numpy as np
import logging

logger = logging.getLogger(__name__)
# inherit from testcase, so we can use assert equal and get expected and observed...
class TestModel(TestCase):
    def test_transect(self):
        transect = Transect(7003800)
        self.assertEqual(transect.x.shape, np.array([]).shape)
    def test_transect_from_opendap(self):
        from django.conf import settings
        settings.NC_RESOURCE = 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/jarkus/profiles/transect.nc'
        transect = makejarkustransect(7003800)['transect']
        self.assertNotEqual(transect.x.shape, np.array([]).shape)
        logger.debug(type(transect.z))
        logger.debug(transect.z.min())
        self.assertTrue(np.alltrue(np.logical_and(transect.z < 50, transect.z > -50)), np.min(transect.z.ravel()))

class TestView(TestCase):
    def setup(self):
        self.client = Client()

    # Create tests for all urls.
    def test_viewer(self):
        resp = self.client.get('/kml/viewer/')
        self.assertEqual(200, resp.status_code)
    def test_lod(self):
        resp = self.client.get('/kml/kml/lod')
        self.assertEqual(200, resp.status_code)
    # def test_areas(self):
    #     resp = self.client.get('/kml/kml/area/?id=1')
    #     self.assertEqual(200, resp.status_code)
    def test_lod_finalbackslash(self):
        resp = self.client.get('/kml/kml/lod/')
        self.assertEqual(200, resp.status_code)
    def test_overview(self):
        resp = self.client.get('/kml/kml/overview')
        self.assertEqual(200, resp.status_code)
        
    def test_transect(self):
        resp = self.client.get('/kml/kml/transect/?id=7003800')
        self.assertEqual(200, resp.status_code)

