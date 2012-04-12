# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.test.client import Client
import nose.tools as nt
from django.test import TestCase
from lizard_kml.models import Transect
import numpy as np

# inherit from testcase, so we can use assert equal and get expected and observed...
class TestModel(TestCase):
    def test_transect(self):
        transect = Transect(7003800)
        self.assertEqual(transect.x.shape, np.array([]).shape)

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

    def test_lod_finalbackslash(self):
        resp = self.client.get('/kml/kml/lod/')
        self.assertEqual(200, resp.status_code)
        
    def test_overview(self):
        resp = self.client.get('/kml/kml/overview')
        self.assertEqual(200, resp.status_code)
        
    def test_transect(self):
        resp = self.client.get('/kml/kml/transect/7003800')
        self.assertEqual(200, resp.status_code)

