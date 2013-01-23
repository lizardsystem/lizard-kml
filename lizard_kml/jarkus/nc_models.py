# (c) Nelen & Schuurmans & Deltares.  GPL licensed, see LICENSE.rst
# Code copied from openearth

# system modules
import bisect
import datetime
from functools import partial
import logging

# numpy/scipy
from numpy import any, all, ma, apply_along_axis, nonzero, array, isnan, logical_or, nan
from numpy.ma import filled
import numpy as np
from scipy.interpolate import interp1d

# pydata
import pandas

# data/gis
import netCDF4
import pyproj

# web
# remain a bit independant from Django settings, so we can test without them
try:
    from django.conf import settings
except ImportError:
    settings = None

logger = logging.getLogger(__name__)

# use Django settings when defined
if settings is not None and hasattr(settings, 'NC_RESOURCE'):
    NC_RESOURCE = settings.NC_RESOURCE
else:
    NC_RESOURCE = {
        'transect': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/jarkus/profiles/transect.nc',
        'BKL_TKL_TND': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/BKL_TKL_MKL/BKL_TKL_TND.nc',
        'DF': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/DuneFoot/DF.nc',
        'MKL': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/BKL_TKL_MKL/MKL.nc',
        'strandbreedte': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/strandbreedte/strandbreedte.nc',
        'strandlijnen': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/strandlijnen/strandlijnen.nc',
        'suppleties': 'http://opendap.deltares.nl/thredds/dodsC/opendap/rijkswaterstaat/suppleties/suppleties.nc',
    }

if '4.1.3' in netCDF4.getlibversion():
    logger.warn('There is a problem with the netCDF 4.1.3 library that causes performance issues for opendap queries, you are using netcdf version {}'.format(netCDF4.getlibversion()))

proj = pyproj.Proj('+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +towgs84=565.237,50.0087,465.658,-0.406857,0.350733,-1.87035,4.0812 +units=m +no_defs')

class NoDataForTransect(Exception):
    def __init__(self, transect_id, closest_transect_id):
        self.transect_id = transect_id
        self.closest_transect_id = closest_transect_id
        message = "Could not find transect data for transect {}, closest is {}".format(transect_id, closest_transect_id)
        super(NoDataForTransect, self).__init__(message)

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
def makejarkustransect(id):
    """Make a transect object, given an id (1000000xareacode + alongshore distance)"""
    id = int(id)
    # TODO: Dataset does not support with ... as dataset, this can lead to too many open ports if datasets are not closed, for whatever reason
    dataset = netCDF4.Dataset(NC_RESOURCE['transect'], 'r')
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
def makejarkuslod():
    dataset = netCDF4.Dataset(NC_RESOURCE['transect'], 'r')
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


# Now for a series of functions that read some datasets about the coast. I'm transforming everything to pandas dataframes
# That way the data looks a bit more relational.
# I'm using uncached versions at the moment. Total query time is about 3seconds on my wifi, which is just a bit too much.
# Optional we can make local copies. Through wired connections it should be a bit faster.

def makeshorelinedf(transect):
    """Read information about shorelines"""
    ds = netCDF4.Dataset(NC_RESOURCE['strandlijnen'], 'r')
    transectidx = bisect.bisect_left(ds.variables['id'], transect)
    if ds.variables['id'][transectidx] != transect:
        idfound = ds.variables['id'][transectidx]
        ds.close()
        raise NoDataForTransect(transect, idfound)
    year = ds.variables['year'][:]
    time = [datetime.datetime(x, 1,1) for x in year]
    mean_high_water = ds.variables['MHW'][transectidx,:]
    mean_low_water = ds.variables['MLW'][transectidx,:]
    dune_foot = ds.variables['DF'][transectidx,:]
    shorelinedf = pandas.DataFrame(
        data=dict(
            time=time, 
            mean_high_water=mean_high_water, 
            mean_low_water=mean_low_water, 
            dune_foot=dune_foot, 
            year=year
            )
        )
    return shorelinedf


def maketransectdf(transect):
    """Read some transect data"""
    ds = netCDF4.Dataset(NC_RESOURCE['transect'], 'r')
    transectidx = bisect.bisect_left(ds.variables['id'],transect)
    if ds.variables['id'][transectidx] != transect:
        idfound = ds.variables['id'][transectidx]
        ds.close()
        raise NoDataForTransect(transect, idfound)
    
    alongshore = ds.variables['alongshore'][transectidx]
    areaname = netCDF4.chartostring(ds.variables['areaname'][transectidx])
    mean_high_water = ds.variables['mean_high_water'][transectidx]
    mean_low_water = ds.variables['mean_low_water'][transectidx]
    ds.close()
    
    transectdf = pandas.DataFrame(index=[transect], data=dict(transect=transect, areaname=areaname, mean_high_water=mean_high_water, mean_low_water=mean_low_water))
    return transectdf


# note that the areaname is a hack, because it is currently missing
def makenourishmentdf(transect, areaname=""):
    """Read the nourishments from the dataset (only store the variables that are a function of nourishment)"""
    
    ds = netCDF4.Dataset(NC_RESOURCE['suppleties'], 'r')
    
    transectidx = bisect.bisect_left(ds.variables['id'],transect)
    if ds.variables['id'][transectidx] != transect:
        idfound = ds.variables['id'][transectidx]
        ds.close()
        raise NoDataForTransect(transect, idfound)
    alongshore = ds.variables['alongshore'][transectidx]
    # TODO fix this name, it's missing
    # areaname = netCDF4.chartostring(ds.variables['areaname'][transectidx,:])
    
    alltypes = set(x.strip() for x in netCDF4.chartostring(ds.variables['type'][:]))
   
    
    # this dataset has data on nourishments and per transect. We'll use the per nourishments, for easier plotting. 
    # skip a few variables that have nasty non-ascii (TODO: check how to deal with non-ascii in netcdf)
    vars = [name for name, var in ds.variables.items() if 'survey' not in name and 'other' not in name and 'nourishment' in var.dimensions]
    vardict = {}
    for var in vars:
        if ('date' in var and 'units' in ds.variables[var].ncattrs()):
            # lookup the time variable
            t = netCDF4.netcdftime.num2date(ds.variables[var], ds.variables[var].units)
            vardict[var] = t
        elif 'stringsize' in ds.variables[var].dimensions:
            vardict[var] = netCDF4.chartostring(ds.variables[var][:])
        else:
            vardict[var] = ds.variables[var][:]
    
    # this is specified in the unit decam, which should be dekam according to udunits specs.
    assert ds.variables['beg_stretch'].units == 'decam'
    ds.close()
    # Put the data in a frame
    nourishmentdf = pandas.DataFrame.from_dict(vardict)
    # Compute nourishment volume in m3/m
    nourishmentdf['volm'] = nourishmentdf['vol']/(10*(nourishmentdf['end_stretch']-nourishmentdf['beg_stretch']))
    
    # Filter by current area and match the area
    filter = reduce(np.logical_and, [
        alongshore >= nourishmentdf.beg_stretch,  
        alongshore < nourishmentdf.end_stretch, 
        nourishmentdf['kustvak'].apply(str.strip)==areaname.tostring().strip()
        ])
    
    nourishmentdfsel = nourishmentdf[filter]
    return nourishmentdfsel


def makemkldf(transect):
    """the momentary coastline data"""
    ds = netCDF4.Dataset(NC_RESOURCE['MKL'], 'r')
    # Use bisect to speed things up
    transectidx = bisect.bisect_left(ds.variables['id'], transect)
    if ds.variables['id'][transectidx] != transect:
        idfound = ds.variables['id'][transectidx]
        ds.close()
        raise NoDataForTransect(transect, idfound)
    
    vars = [name for name, var in ds.variables.items() if var.dimensions == ('time', 'alongshore')]
    # Convert all variables that are a function of time to a dataframe
    vardict = dict((var, ds.variables[var][:,transectidx]) for var in vars)
    vardict['time'] = netCDF4.netcdftime.num2date(ds.variables['time'], ds.variables['time'].units)
    # Deal with nan's in an elegant way:
    mkltime = ds.variables['time_MKL'][:,transectidx]
    mkltime = np.ma.masked_array(mkltime, mask=np.isnan(mkltime))
    vardict['time_MKL'] = netCDF4.netcdftime.num2date(mkltime, ds.variables['time_MKL'].units)
    ds.close()
    mkldf =  pandas.DataFrame(vardict)
    mkldf = mkldf[np.logical_not(pandas.isnull(mkldf['time_MKL']))]
    return mkldf


def makebkldf(transect):
    """the basal coastline data"""
    ds = netCDF4.Dataset(NC_RESOURCE['BKL_TKL_TND'], 'r')
    # Use bisect to speed things up
    transectidx = bisect.bisect_left(ds.variables['id'], transect)
    if ds.variables['id'][transectidx] != transect:
        idfound = ds.variables['id'][transectidx]
        ds.close()
        raise NoDataForTransect(transect, idfound)
    
    vars = [name for name, var in ds.variables.items() if var.dimensions == ('time', 'alongshore')]
    # Convert all variables that are a function of time to a dataframe
    vardict = dict((var, ds.variables[var][:,transectidx]) for var in vars)
    vardict['time'] = netCDF4.netcdftime.num2date(ds.variables['time'], ds.variables['time'].units)
    ds.close()
    bkldf =  pandas.DataFrame(vardict)
    return bkldf


def makebwdf(transect):
    # Now read the beachwidth data.
    ds = netCDF4.Dataset(NC_RESOURCE['strandbreedte'], 'r')
    # Use bisect to speed things up
    transectidx = bisect.bisect_left(ds.variables['id'], transect)
    if ds.variables['id'][transectidx] != transect:
        idfound = ds.variables['id'][transectidx]
        ds.close()
        raise NoDataForTransect(transect, idfound)
    
    vars = [name for name, var in ds.variables.items() if var.dimensions == ('time', 'alongshore')]
    # Convert all variables that are a function of time to a dataframe
    vardict = dict((var, ds.variables[var][:,transectidx]) for var in vars)
    vardict['time'] = netCDF4.netcdftime.num2date(ds.variables['time'], ds.variables['time'].units)
    ds.close()
    bwdf =  pandas.DataFrame(vardict)
    return bwdf


def makedfdf(transect):
    """read the dunefoot data"""
    ds = netCDF4.Dataset(NC_RESOURCE['DF'], 'r')
    
    # Use bisect to speed things up
    transectidx = bisect.bisect_left(ds.variables['id'], transect)
    if ds.variables['id'][transectidx] != transect:
        idfound = ds.variables['id'][transectidx]
        ds.close()
        raise NoDataForTransect(transect, idfound)
    
    vars = [name for name, var in ds.variables.items() if var.dimensions == ('alongshore', 'time')]
    # Convert all variables that are a function of time to a dataframe
    # Note inconcsiste dimension ordering
    vardict = dict((var, ds.variables[var][transectidx,:]) for var in vars)
    vardict['time'] = netCDF4.netcdftime.num2date(ds.variables['time'], ds.variables['time'].units)
    ds.close()
    dfdf =  pandas.DataFrame(vardict)
    return dfdf


def makedfs(transect):
    """create dataframes for coastal datasets available from openearth"""
    # We could do this in a multithreading pool to speed up, but not for now.
    shorelinedf = makeshorelinedf(transect)
    transectdf = maketransectdf(transect)
    nourishmentdf = makenourishmentdf(transect, areaname=transectdf['areaname'].irow(0))
    mkldf = makemkldf(transect)
    bkldf = makebkldf(transect)
    bwdf = makebwdf(transect)
    dfdf = makedfdf(transect)
    return dict(
        shorelinedf=shorelinedf,
        transectdf=transectdf,
        nourishmentdf=nourishmentdf,
        mkldf=mkldf,
        bkldf=bkldf,
        bwdf=bwdf,
        dfdf=dfdf
        )
