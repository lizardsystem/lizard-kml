# (c) Nelen & Schuurmans.  GPL licensed, see LICENSE.txt.
from django.db import models
from django.utils.translation import ugettext_lazy as _
import netCDF4
import datetime

class KmlType(models.Model):
    """
    A category of KML files, for example "Jarkusprofielen" or "Vaklodingen".
    One KmlType contains KML files for many Area's.
    """

    name = models.CharField(_('name'), max_length=40)
    description = models.TextField(_('description'), null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ('name', )

class Area(models.Model):
    """
    An area, for example "Walcheren" or "Maasvlakte", and an URL to its corresponding KML file.
    """

    name = models.CharField(_('name'), max_length=40)
    description = models.TextField(_('description'), null=True, blank=True)
    url = models.CharField(_('url'), max_length=200, blank=True, null=True)
    kml_type = models.ForeignKey('KmlType', null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ('name', )

# Copied from openearthtools/kmldap
from numpy import any, all, ma, apply_along_axis, nonzero, array, isnan
from scipy.interpolate import interp1d
from functools import partial

class Transect(object):
    """Transect that has coordinates and time"""
    def __init__(self, id):
        self.id = id
        # x and y can be lat,lon, we don't care here...
        self.x = array([])
        self.y = array([])
        self.z = array([])
        self.t = array([])
        # Cross shore is the local (engineering) coordinate system
        # or engineering datum, see for example:
        # http://en.wikipedia.org/wiki/Datum_(geodesy)#Engineering_datums
        self.cross_shore = array([])

    def begindates(self):
        return [date for date in self.t]
    def enddates(self):
        return [date.replace(year=date.year+1) for date in self.t]

    def interpolate_z(self):
        """interpolate over missing z values"""
        if not self.z.any():
            return self.z
        def fillmissing(x,y):
            """fill nans in y using linear interpolation"""
            f = interp1d(x[~isnan(y)], y[~isnan(y)], kind='linear',bounds_error=False, copy=True)
            new_y = f(list(x)) #some bug causes it not to work if x is passed directly
            return new_y
        # define an intorpolation for a row by partial function application
        rowinterp = partial(fillmissing, self.cross_shore)
        # apply to rows (along columns)
        z = apply_along_axis(rowinterp, 1, self.z)
        # mask missings
        z = ma.masked_array(z, mask=isnan(z))
        return z


class PointCollection(object):
    def __init__(self):
        self.id = array([])
        self.x = array([])
        self.y = array([])
        self.z = array([])

# Some factory functions, because the classes are dataset unaware (they were also used by other EU countries)
# @cache.beaker_cache('id', expire=60)

# TODO: move these to a configuration file ...
NC_RESOURCE = 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/jarkus/profiles/transect.nc'
# optional, download local: wget http://opendap.deltares.nl/thredds/fileServer/opendap/rijkswaterstaat/jarkus/profiles/transect.nc

def makejarkustransect(id):
    """Make a transect object, given an id (1000000xareacode + alongshore distance)"""
    url = NC_RESOURCE
    # TODO: Dataset does not support with ... as dataset, this can lead to too many open ports if datasets are not closed, for whatever reason
    dataset = netCDF4.Dataset(url)
    tr = Transect(id)

    # Opendap is index based, so we have to do some numpy tricks to get the data over (and fast)
    # read indices for all years (only 50 or so), takes 0.17 seconds on my wireless
    years = dataset.variables['time'][:]
    # read all indices (this would be nice to cache)... takes 0.24 seconds on my wireless
    id = dataset.variables['id'][:] 
    alongshoreindex = nonzero(id == tr.id)
    alongshoreindex = alongshoreindex[0][0]
    lon = dataset.variables['lon'][alongshoreindex,:] 
    lat = dataset.variables['lat'][alongshoreindex,:] 
    #filter out the missing to make it a bit smaller
    z = dataset.variables['altitude'][:,alongshoreindex,:]
    filter = z == dataset.variables['altitude']._FillValue # why are missings not taken into account?
    z[filter] = None
    # convert to datetime objects. (netcdf only stores numbers, we use years here (ignoring the measurement date))
    t = array([datetime.datetime.fromtimestamp(days*3600*24) for days in years])
    cross_shore = dataset.variables['cross_shore'][:]
    # leave out empty crossections and empty dates
    tr.lon = lon[(~filter).any(0)]
    tr.lat = lat[(~filter).any(0)]
    # keep what is not filtered in 2 steps 
    #         [over x            ][over t            ]
    tr.z = z[:,(~filter).any(0)][(~filter).any(1),:] 
    tr.t = t[(~filter).any(1)]
    tr.cross_shore = cross_shore[(~filter).any(0)]

    # get the water level variables
    mhw = dataset.variables['mean_high_water'][alongshoreindex]
    mlw = dataset.variables['mean_low_water'][alongshoreindex]
    tr.mhw = mhw.squeeze()
    tr.mlw = mlw.squeeze()

    dataset.close()
    return tr

#TODO: @cache.beaker_cache(None, expire=600)

def makejarkusoverview():
    url = NC_RESOURCE
    dataset = netCDF4.Dataset(url)
    points = PointCollection()
    id = dataset.variables['id'][:] # ? why
    # Get the locations of the beach poles..
    lon = dataset.variables['rsp_lon'][:] #[:,rsp] #? can this be done simpler?
    lat = dataset.variables['rsp_lat'][:] #[:,rsp] #?
    points.id = id
    points.lon = lon
    points.lat = lat
    dataset.close()
    return points
    
