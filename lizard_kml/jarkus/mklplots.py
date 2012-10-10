# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>
import bisect
import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas
import statsmodels.api as sm
import netCDF4

# Define url's to relevant databases
mklurl = '/Users/fedorbaart/Downloads/MKL.nc'
nourishmenturl = '/Users/fedorbaart/Downloads/suppleties.nc'
transecturl = '/Users/fedorbaart/Downloads/transect.nc'

# Function arguments.
transect = 7004000

# Read dataset and transform to dataframe
ds = netCDF4.Dataset(transecturl)
transectidx = bisect.bisect_left(ds.variables['id'],transect)
alongshore = ds.variables['alongshore'][transectidx]
areaname = netCDF4.chartostring(ds.variables['areaname'][transectidx])
print areaname
ds.close()

# Read the nourishments from the dataset (only store the variables that are a function of nourishment)
ds = netCDF4.Dataset(nourishmenturl)
vars = [name for name, var in ds.variables.items() if 'nourishment' in var.dimensions]
vardict = {}
for var in vars:
    if ('date' in var):
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
    [x.strip() == str(areaname).strip() for x in nourishmentdf['kustvak'].tolist()]
    ])
nourishmentdfsel = nourishmentdf[filter]

# Now read the mkl data.
ds = netCDF4.Dataset(mklurl)
# Use bisect to speed things up
transectidx = bisect.bisect_left(ds.variables['id'], transect)
vars = [name for name, var in ds.variables.items() if var.dimensions == ('time', 'alongshore')]
# Convert all variables that are a function of time to a dataframe
vardict = dict((var, ds.variables[var][:,transectidx]) for var in vars)
vardict['time'] = netCDF4.netcdftime.num2date(ds.variables['time'], ds.variables['time'].units)
ds.close()
mkldf =  pandas.DataFrame(vardict)

# Build a statistical model

import statsmodels.tsa
filter = ~np.isnan(mkldf['momentary_coastline'])
vals = np.asarray(mkldf[filter]['momentary_coastline'])
dates= [(x - datetime.datetime(1970,1,1)).total_seconds()*365.25*3600*24.0 for x in mkldf[filter]['time'].tolist()]
model = statsmodels.tsa.arima_model.ARMA(vals, dates=mkldf[filter]['time'], freq='A')
result = model.fit(order=(1,0))

# Plot the results.

fig, ax1 = plt.subplots(1,1)
ax1.plot(mkldf['time'][:], mkldf['momentary_coastline'][:])
ax1.set_ylabel('Nourishment volume [m]')
ax2 = ax1.twinx()
ax2.plot(nourishmentdfsel['time'], nourishmentdfsel['momentary_coastline'])
ax2.set_xlabel('time')
ax2.set_ylabel("{} [{}]".format(ds.variables['momentary_coastline'].long_name, ds.variables['momentary_coastline'].units))


