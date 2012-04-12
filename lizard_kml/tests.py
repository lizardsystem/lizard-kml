# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.test.client import Client
import nose.tools as nt

def test():
    assert True

class TestView(object):
    def setup(self):
        self.client = Client()

    # Create tests for all urls.
    def test_viewer(self):
        resp = self.client.get('/kml/viewer/')
        assert resp.status_code == 200

    def test_kml1(self):
        resp = self.client.get('/kml/kml/')
        assert resp.status_code == 200
        
    def test_kml2(self):
        resp = self.client.get('/kml/kml/lod/')
        assert resp.status_code == 200
        
    def test_kml3(self):
        resp = self.client.get('/kml/kml/overview/')
        assert resp.status_code == 200
        
    def test_kml4(self):
        resp = self.client.get('/kml/kml/transect/7003800/')
        assert resp.status_code == 200
