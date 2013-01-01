# (c) Nelen & Schuurmans & Deltares.  GPL licensed, see LICENSE.rst.
# Code copied from openearth
import itertools
import cStringIO
import functools
import logging

import numpy
import numpy as np
from numpy import isnan, hstack, newaxis, zeros
from numpy.ma import filled, masked_array

import scipy.interpolate

from matplotlib import pyplot
from matplotlib import text
from matplotlib import colors
from matplotlib.dates import mx2num, date2num
import matplotlib.ticker
import matplotlib.collections
import matplotlib.cm as cm

import netCDF4
import netcdftime

from lizard_kml.jarkus import extra_cm

from django.conf import settings

logger = logging.getLogger(__name__)

class WouldTakeTooLong(Exception):
    pass

class TimeStagNormalize(colors.Normalize):
    def inverse(self, value):
        result_value = colors.Normalize.inverse(self, value)
        print value, '=', result_value
        return result_value

def jarkustimeseries(transect, plotproperties=None):
    """create a timeseries plot for a transect"""
    if plotproperties is None:
        plotproperties = {}
    # interpolation function
    z = transect.interpolate_z()
    # create the plot
    if len(z.shape) != 2:
        raise ValueError('Z should be of dim 2')
    # use a fixed min, max for color interpolation, we have no green on beaches but it shows a lot of contrast
    # TODO: Make this stateless.... (only call methods on figures and axes)
    fig = pyplot.figure(figsize=(4, 3))
    plot = fig.add_subplot(111)
    mappable = plot.pcolor(transect.cross_shore, date2num(transect.t), z, vmin=-20, vmax=20, cmap=extra_cm.GMT_drywet_r)
    #mappable = plot.pcolor(transect.cross_shore, date2num(transect.t), z, norm=TimeStagNormalize(), cmap=extra_cm.GMT_drywet_r)
    bar = fig.colorbar(mappable)
    # setup date ticks, maybe this can be done shorter
    datelocator = matplotlib.dates.AutoDateLocator()
    dateformatter = matplotlib.dates.AutoDateFormatter(datelocator)
    plot.yaxis.set_major_formatter(dateformatter)
    plot.set_xlabel('Cross shore distance [m]')
    plot.set_ylabel('Measurement time [y]')
    for o in plot.findobj(text.Text):
        o.set_size('xx-small')
    for o in mappable.colorbar[1].findobj(text.Text):
        o.set_size('xx-small')

    buf = cStringIO.StringIO()
    fig.savefig(buf, **plotproperties)
    buf.seek(0)
    # cleanup
    fig.clf()
    # return an 'open' file descriptor
    return buf

def eeg(transect, plotproperties=None):
    """plot eeg like plot of transects"""

    if plotproperties is None:
        plotproperties = {}
    # from http://matplotlib.sourceforge.net/examples/pylab_examples/mri_with_eeg.html
    # get axes
    t = date2num(transect.t)
    x = transect.cross_shore
    # and data
    z = transect.interpolate_z()
    nrows, nsamples = z.shape

    # create a line for each timeseries
    segs = []
    ticklocs = []
    for i, row in enumerate(z):
        # add a line, scale it by the y axis each plot has a range of de elevation divided by 7.5 (~2 years up and down)
        segs.append(hstack((x[:,newaxis], z[i,:,newaxis]*365.0/7.5)))
        ticklocs.append(t[i]) # use date for yloc
    # create an offset for each line
    offsets = zeros((nrows,2), dtype=float)
    offsets[:,1] = ticklocs
    # create the lines
    lines = matplotlib.collections.LineCollection(segs, offsets=offsets)
    # create a new figure
    fig = pyplot.figure(figsize=(4, 3))
    # add axes
    plot = fig.add_subplot(111)
    # add the lines
    plot.add_collection(lines)
    # set the x axis
    plot.set_xlim(transect.cross_shore.min(), transect.cross_shore.max())
    # set the y axis (add a bit of room cause the wiggles go over a few years)
    plot.set_ylim(t.min()-730,t.max()+730)
    for o in plot.findobj(text.Text):
        o.set_size('xx-small')
    datelocator = matplotlib.dates.AutoDateLocator()
    dateformatter = matplotlib.dates.AutoDateFormatter(datelocator)
    plot.yaxis.set_major_formatter(dateformatter)

    buf = cStringIO.StringIO()
    fig.savefig(buf, **plotproperties)
    buf.seek(0)
    # cleanup
    fig.clf()
    # return an 'open' file descriptor
    return buf


def fill_z(x, z):
    # Interpolate over time and space
    cross_shore = x
    filled = []
    # Space first
    for i in xrange(z.shape[0]):
        z_idx = ~(z[i,:].mask)
        interp = scipy.interpolate.interp1d(cross_shore[z_idx], z[i,z_idx], bounds_error=False)
        zinterp = interp(cross_shore)
        filled.append(zinterp)
    zfilled = masked_array(filled, mask=np.isnan(np.array(filled)))

    # Fill up with old or new data
    for i in xrange(zfilled.shape[1]):
        a = zfilled[:,i]
        xp = np.arange(len(a))
        if not a.mask.all():
            zfilled[:,i] = scipy.interp(xp, xp[~a.mask], a[~a.mask])
    return zfilled

def timeplot(plot, cross_shore, zfilled, timenum, sm, plotlatest=False):
    # loop from last to first counting backwards
    for i in xrange(-1,-1*zfilled.shape[0]+1,-1):
        t = timenum[-i]
        minz = np.nanmin(
            zfilled[-1:-i:-1,:],
            axis=0
            )
        plot.fill_between(
            cross_shore,
            minz,
            zfilled[-i,:],
            alpha=0.3,
            color=sm.to_rgba(t),
            where=minz > zfilled[-i,:],
            interpolate=True,
            linewidth=0
            )
    if (plotlatest):
        plot.plot(cross_shore, zfilled[-1,:],'k-', alpha=0.5, linewidth=1)

def jarkusmean(id_min, id_max, plotproperties=None):
    id_min = int(id_min)
    id_max = int(id_max)
    dataset = netCDF4.Dataset(settings.NC_RESOURCE['transect'], 'r')
    try:
        # Lookup variables
        ids_all = dataset.variables['id'][:]
        # idx, = (id == 7004000).nonzero()
        ids = ((ids_all < id_max) & (ids_all > id_min)).nonzero()[0]
        if len(ids) > 15:
            raise WouldTakeTooLong()
        timevar = dataset.variables['time']
        time = netcdftime.num2date(timevar[:], timevar.units)
        cross_shore = dataset.variables['cross_shore'][:]

        # Define color for years
        timenum = matplotlib.dates.date2num(time)
        sm = matplotlib.cm.ScalarMappable(cmap=matplotlib.cm.jet)
        sm.set_clim(np.min(timenum), np.max(timenum))
        sm.set_array(timenum)

        # Create the plot
        fig = pyplot.figure()
        plot = fig.add_subplot(111)
        for i, id in enumerate(ids):
            z = dataset.variables['altitude'][:,id,:]
            if z.mask.all(1).any():
                continue
            logger.debug('Plotting %s', id)
            zfilled = fill_z(cross_shore, z+i*4)
            timeplot(plot, cross_shore, zfilled, timenum, sm)
    finally:
        dataset.close()

    # Format the colorbar
    cb = fig.colorbar(sm)
    yearsfmt = matplotlib.dates.DateFormatter('%Y')
    yearsloc = matplotlib.dates.YearLocator()
    #cb.locator = yearsloc
    cb.formatter = yearsfmt
    cb.update_ticks()

    plot.set_xlim(-500, 1000)

    # save image
    buf = cStringIO.StringIO()
    fig.savefig(buf, **plotproperties)
    buf.seek(0)

    # cleanup
    fig.clf()
    # return an 'open' file descriptor
    return buf
