# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.

from django.test import TestCase


class ViewsTest(TestCase)
    # Create tests for all urls.
    def test_index(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
    def test_kml(self):
        resp = self.client.get('/kml')
        self.assertEqual(resp.status_code, 200)
    def test_kml(self):
        resp = self.client.get('/kml/lod')
        self.assertEqual(resp.status_code, 200)
    def test_kml(self):
        resp = self.client.get('/kml/overview')
        self.assertEqual(resp.status_code, 200)
    def test_kml(self):
        resp = self.client.get('/kml/transect/7003800')
        self.assertEqual(resp.status_code, 200)
