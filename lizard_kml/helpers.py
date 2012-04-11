# by convention.
import cStringIO
import numpy as np
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
    """
    convert the coordinates to a string so they can be used by kml

    # Example usage:
    >>> x = np.array([1,1,1])
    >>> y = np.array([1,-2e10,3.0000001])
    >>> print(textcoordinates(x, y))
    1.0,1.0,0.0
    1.0,-20000000000.0,0.0
    1.0,3.0000001,0.0
    <BLANKLINE>

    """
    if z is None:
        z = np.zeros(x.shape)
    coordinates = np.vstack([x, y, z]).T
    # only write coordinates where none is nan
    filter = np.isnan(coordinates).any(1)
    # use cStringIO for performance
    output = cStringIO.StringIO()
    # save coordinates to string buffer
    # I think this is faster than other methods
    # Use %s to get reduced string output
    np.savetxt(output, coordinates[~filter],delimiter=',',fmt='%s' )
    return output.getvalue()

def kmldate(date):
    """
    print date in kml format

    # Example usage
    >>> import datetime
    >>> date = datetime.datetime.fromtimestamp(0)
    >>> # this breaks if tzdata changed after 1970, pff
    >>> date = datetime.datetime(year=2000, month=1, day=1)
    >>> kmldate(date)
    '2000-01-01T00:00:00Z'

    """
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")
