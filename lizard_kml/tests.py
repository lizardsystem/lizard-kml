# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf import settings
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

    def test_settings(self):
        self.assertNotEqual(settings.NC_RESOURCE, None)

    def test_transect_from_opendap(self):
        # Test a transect data from opendap...
        # TODO: When I run the tests this is not defined otherwise...
        # settings.NC_RESOURCE = 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/jarkus/profiles/transect.nc'
        # n.b.: ejnens: works for me
        transect = makejarkustransect(7003800)
        self.assertNotEqual(transect.x.shape, np.array([]).shape)
        self.assertTrue(
            np.alltrue(
                # Everything should be nan or in expected range
                np.logical_or(
                    np.isnan(transect.z),
                    # numpy arrays don't support:
                    # -50 < x < 50
                    np.logical_and(
                        # bathymetry and topography should be within this range....
                        transect.z < 50,
                        transect.z > -50)
                    )
                )
            )


class TestView(TestCase):
    def setup(self):
        self.client = Client()

    # Create tests for all urls.
    # Trailing slashes should be 'stable' as discussed by the following article:
    # http://googlewebmastercentral.blogspot.com/2010/04/to-slash-or-not-to-slash.html
    # Other Lizard components seem to prefer trailing slashes, so
    # check for code 301 for URLs without a trailing slash,
    # and code 200 for URLs with a trailing slash.

    def test_viewer_noslash(self):
        resp = self.client.get('/kml/viewer')
        self.assertEqual(301, resp.status_code)

    def test_viewer_slash(self):
        resp = self.client.get('/kml/viewer/')
        self.assertEqual(200, resp.status_code)

    def test_lod_noslash(self):
        resp = self.client.get('/kml/kml/lod')
        self.assertEqual(301, resp.status_code)

    def test_lod_slash(self):
        resp = self.client.get('/kml/kml/lod/')
        self.assertEqual(200, resp.status_code)

    # def test_areas(self):
    #     resp = self.client.get('/kml/kml/area/?id=1')
    #     self.assertEqual(200, resp.status_code)

    def test_overview_noslash(self):
        resp = self.client.get('/kml/kml/overview')
        self.assertEqual(301, resp.status_code)

    def test_overview_slash(self):
        resp = self.client.get('/kml/kml/overview/')
        self.assertEqual(200, resp.status_code)

    def test_transect_noslash(self):
        resp = self.client.get('/kml/kml/transect/7003800')
        self.assertEqual(301, resp.status_code)

    def test_transect_slash(self):
        resp = self.client.get('/kml/kml/transect/7003800/')
        self.assertEqual(200, resp.status_code)

    def test_transect_info(self):
        resp = self.client.get('/kml/info/7003800/')
        self.assertEqual(200, resp.status_code)
    def test_transect_xls(self):
        resp = self.client.get('/kml/xls/7003800/')
        self.assertEqual(200, resp.status_code)

    def test_transect_query_noslash(self):
        resp = self.client.get('/kml/kml/transect/7003800?exaggeration=100&lift=100')
        self.assertEqual(301, resp.status_code)

    def test_transect_query_slash(self):
        resp = self.client.get('/kml/kml/transect/7003800/?exaggeration=100&lift=100')
        self.assertEqual(200, resp.status_code)
