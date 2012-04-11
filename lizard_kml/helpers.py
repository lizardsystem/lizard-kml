# copied from openearthtools/kmldap
def compress_kml(kml):
    "Returns compressed KMZ from the given KML string."
    import cStringIO, zipfile
    kmz = cStringIO.StringIO()
    zf = zipfile.ZipFile(kmz, 'a', zipfile.ZIP_DEFLATED)
    # kmz file is a zip file that contains a doc.kml file
    zf.writestr('doc.kml', kml)
    zf.close()
    kmz.seek(0)
    return kmz.read()

def textcoordinates(x,y,z=None):
    """print the coordinates so they can be used by kml"""
    import cStringIO
    import numpy
    if z is None:
        z = numpy.zeros(x.shape)
    coordinates = numpy.vstack([x, y, z]).T
    # only write coordinates where none is nan
    filter = numpy.isnan(coordinates).any(1)
    # use cStringIO for performance
    output = cStringIO.StringIO()
    # save coordinates to string buffer
    numpy.savetxt(output, coordinates[~filter],delimiter=',' )
    # revert and print....
    output.seek(0)
    return output.read()

def kmldate(date):
    """print date in kml format"""
    # something like....
    # 1970-01-01T00:00:00Z
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")
