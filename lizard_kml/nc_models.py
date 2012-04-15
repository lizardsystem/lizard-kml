from django.conf import settings
import netCDF4
import datetime

# Copied from openearthtools/kmldap
from numpy import any, all, ma, apply_along_axis, nonzero, array, isnan, logical_or, nan
from numpy.ma import filled
import numpy as np
from scipy.interpolate import interp1d
from functools import partial

import logging
logger = logging.getLogger(__name__)

if '4.1' in netCDF4.getlibversion():
    logger.warn('There is a problem with the netCDF 4.1.3 library that causes performance issues for opendap queries, you are using netcdf version {}'.format(netCDF4.getlibversion()))
    
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
    lon0 = dataset.variables['lon'][:,1] 
    lat0 = dataset.variables['lat'][:,1]
    lon1 = dataset.variables['lon'][:,-1]
    lat1 = dataset.variables['lat'][:,-1]
    overview['lon0'] = lon0
    overview['lon1'] = lon1
    overview['lat0'] = lat0
    overview['lat1'] = lat1
    overview['north'] = np.maximum(lat0, lat1)
    overview['south'] = np.minimum(lat0, lat1)
    # not circle safe...
    overview['east'] = np.maximum(lon0, lon1)
    overview['west'] = np.minimum(lon0, lon1)
    overview['id'] = id
    dataset.close()
    # return dict to conform to the "rendering context"
    return overview
