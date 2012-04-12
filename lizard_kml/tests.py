# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.test.client import Client
import nose.tools as nt

def test():
    1/0

class TestView(object):
    def setup(self):
        self.client = Client()

    # Create tests for all urls.
    def test_viewer(self):
        resp = self.client.get('/kml/viewer/')
        assert resp.status_code == 200

    def test_kml(self):
        resp = self.client.get('/kml/kml/')
        assert resp.status_code == 200
        
    def test_lod(self):
        resp = self.client.get('/kml/kml/lod/')
        assert resp.status_code == 200
        
    def test_overview(self):
        resp = self.client.get('/kml/kml/overview/')
        assert resp.status_code == 200
        
    def test_transect(self):
        resp = self.client.get('/kml/kml/transect/7003800/')
        assert resp.status_code == 200
