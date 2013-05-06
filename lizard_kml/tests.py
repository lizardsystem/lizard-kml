# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.conf import settings
from django.test.client import Client
from django.test import TestCase
import nose.tools as nt

from lizard_kml.jarkus.nc_models import Transect, makejarkustransect

import numpy as np
import logging


logger = logging.getLogger(__name__)


# inherit from testcase, so we can use assert equal and get expected and observed...
class TestModel(TestCase):
    def test_transect(self):
        transect = Transect(7003800)
        self.assertEqual(transect.x.shape, np.array([]).shape)

    def test_settings(self):
        self.assertNotEqual(settings.NC_RESOURCE['transect'], None)

    def test_transect_from_opendap(self):
        # Test a transect data from opendap...
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

    def test_viewer(self):
        resp = self.client.get('/')
        self.assertEqual(200, resp.status_code)

    def test_lod(self):
        resp = self.client.get('/jarkuskml/lod/')
        self.assertEqual(200, resp.status_code)

    # def test_areas(self):
    #     resp = self.client.get('/kml/area/?id=1')
    #     self.assertEqual(200, resp.status_code)

    def test_overview(self):
        resp = self.client.get('/jarkuskml/overview/')
        self.assertEqual(200, resp.status_code)

    def test_transect(self):
        resp = self.client.get('/jarkuskml/transect/7003800/')
        self.assertEqual(200, resp.status_code)

    def test_transect_info(self):
        resp = self.client.get('/info/7003800/')
        self.assertEqual(200, resp.status_code)

    def test_transect_xls(self):
        resp = self.client.get('/xls/7003800/')
        self.assertEqual(200, resp.status_code)

    def test_transect_query(self):
        resp = self.client.get('/jarkuskml/transect/7003800/?exaggeration=100&lift=100')
        self.assertEqual(200, resp.status_code)
