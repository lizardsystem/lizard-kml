# (c) Nelen & Schuurmans & Deltares.  GPL licensed, see LICENSE.rst
# Code copied from openearth
from django.conf import settings
import netCDF4
import datetime

# Copied from openearthtools/kmldap
from numpy import any, all, ma, apply_along_axis, nonzero, array, isnan, logical_or, nan
from numpy.ma import filled
import numpy as np
from scipy.interpolate import interp1d
from functools import partial

import pyproj
import logging
logger = logging.getLogger(__name__)

if '4.1.3' in netCDF4.getlibversion():
    logger.warn('There is a problem with the netCDF 4.1.3 library that causes performance issues for opendap queries, you are using netcdf version {}'.format(netCDF4.getlibversion()))

proj = pyproj.Proj('+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs')

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
    
    def move_by(self, distance):
        """
        Move the x,y coordinates by distance, perpendicular, assuming that they are lat,lon and that we can move in EPSG:28992
        
        >>> t = Transect(0) 
        >>> t.x = array([4.0])
        >>> t.y = array([51.0])
        >>> x,y = t.move_by(1000)
        >>> x, y  # doctest:+ELLIPSIS
        (array([ 3.999...]), array([ 51.0089...]))
        """
        # project from wgs84 to rd, assuming x,y are lon, lat
        # compute the angle from the transect coordinates
        
        x,y = proj(self.x, self.y)
        
        dx = self.x[-1] - self.x[0]
        dy = self.y[-1] - self.y[0]
        angle = np.arctan2(dy,dx) + np.pi*0.5 # rotate by 90 degrees
        
        x += distance * np.cos(angle);
        y += distance * np.sin(angle);
        lon, lat = proj(x,y,inverse=True)
        return lon, lat


# Some factory functions, because the classes are dataset unaware (they were also used by other EU countries)
# @cache.beaker_cache('id', expire=60)
def makejarkustransect(id, **args):
    """Make a transect object, given an id (1000000xareacode + alongshore distance)"""
    id = int(id)
    # TODO: Dataset does not support with ... as dataset, this can lead to too many open ports if datasets are not closed, for whatever reason
    dataset = netCDF4.Dataset(settings.NC_RESOURCE)
    tr = Transect(id)

    # Opendap is index based, so we have to do some numpy tricks to get the data over (and fast)
    # read indices for all years (only 50 or so), takes 0.17 seconds on my wireless
    years = dataset.variables['time'][:]
    # days = dataset.variables['time']
    # TODO: dates = netcdftime.num2date(days, days.units)
    # read all indices (this would be nice to cache)... takes 0.24 seconds on my wireless
    id = dataset.variables['id'][:] 
    alongshoreindex = nonzero(id == tr.id)
    alongshoreindex = alongshoreindex[0][0]
    lon = dataset.variables['lon'][alongshoreindex,:] 
    lat = dataset.variables['lat'][alongshoreindex,:] 
    #filter out the missing to make it a bit smaller
    z = dataset.variables['altitude'][:,alongshoreindex,:]
    # why are missings not taken into account?, just in case also filter out fill value.
    filter = logical_or(
        isnan(z),
        z == dataset.variables['altitude']._FillValue
        )
    # Convert from masked to regular array
    z = filled(z, nan)
    # Make sure we set all missings and nans to nan 
    z[filter] = nan
    # convert to datetime objects. (netcdf only stores numbers, we use years here (ignoring the measurement date))
    t = array([datetime.datetime.fromtimestamp(days*3600*24) for days in years])
    cross_shore = dataset.variables['cross_shore'][:]
    # leave out empty crossections and empty dates
    tr.lon = lon[(~filter).any(0)]
    tr.lat = lat[(~filter).any(0)]
    # use lat, lon as x here...
    tr.x = tr.lon
    tr.y = tr.lat
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
    # return dict to conform to the "rendering context"

    
    tr.lon, tr.lat
    return tr

#TODO: @cache.beaker_cache(None, expire=600)
def makejarkusoverview():
    dataset = netCDF4.Dataset(settings.NC_RESOURCE, 'r')
    overview = {}
    # Get the locations of the beach transect lines..
    # For some reason index 0 leads to the whole variable being send over.
    # TODO: bug in netCDF4 + 4.1.3 library opendap index 0 with nc_get_vara doesn't use index....
    # Make sure you use netcdf >=4.2

    id = dataset.variables['id'][:]
    lon0 = dataset.variables['lon'][:,0]
    lat0 = dataset.variables['lat'][:,1]
    lon1 = dataset.variables['lon'][:,-1]
    lat1 = dataset.variables['lat'][:,-1]
    overview['lon0'] = lon0
    overview['lon1'] = lon1
    overview['lat0'] = lat0
    overview['lat1'] = lat1
    rsp_lon = dataset.variables['rsp_lon'][:] 
    rsp_lat = dataset.variables['rsp_lat'][:]

    # few 
    overview['north'] = rsp_lat + 0.002
    overview['south'] = rsp_lat - 0.002

    # HACK: not circle safe...
    overview['east'] = rsp_lon + .0025
    overview['west'] = rsp_lon - .0025
    overview['id'] = id
    dataset.close()
    # return dict to conform to the "rendering context"
    return overview
