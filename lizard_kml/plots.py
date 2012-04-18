# Code copied from openearthtools
import itertools
import cStringIO
import functools
import logging
from threading import Lock

import numpy
from numpy import ma
from numpy import isnan, hstack, newaxis, zeros

import scipy.interpolate

import matplotlib
# use in memory backend
matplotlib.use('Agg')

from matplotlib import pyplot as p
from matplotlib import text
from matplotlib.dates import mx2num, date2num
import matplotlib.ticker
import matplotlib.collections
import matplotlib.cm as cm

import extra_cm

log = logging.getLogger(__name__)
pylablock = Lock()

def jarkustimeseries(transect, plotproperties=None):
    """create a timeseries plot for a transect"""
    if plotproperties is None:
        plotproperties = {}
    f = cStringIO.StringIO()
    
    # interpolation function
    z = transect.interpolate_z()
    # create the plot
    if len(z.shape) != 2:
        raise ValueError('Z should be of dim 2')
    # use a fixed min, max for color interpolation, we have no green on beaches but it shows a lot of contrast
    # HACK: uses a lock....
    # pylab is stateful, we don't want to call it from multiple threads at the same time
    pylablock.acquire()
    try:
        # TODO: Make this stateless.... (only call methods on figures and axes)
        p.figure(figsize=(3, 2))
        fig = p.pcolor(transect.cross_shore, date2num(transect.t), z, vmin=-20, vmax=20, cmap=extra_cm.GMT_drywet_r)
        p.colorbar()
        # setup date ticks, maybe this can be done shorter
        datelocator = matplotlib.dates.AutoDateLocator()
        dateformatter = matplotlib.dates.AutoDateFormatter(datelocator)
        fig.axes.yaxis.set_major_formatter(dateformatter)
        fig.axes.set_xlabel('Cross shore distana.set_colorbarce [m]')
        fig.axes.set_ylabel('Measurement time [y]')
        for o in fig.axes.findobj(text.Text):
            o.set_size('xx-small')
        for o in fig.colorbar[1].findobj(text.Text):
            o.set_size('xx-small')
        p.savefig(f, **plotproperties)
    finally:
        pylablock.release()
    f.seek(0)
    return f

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
    pylablock.acquire()
    try:
        f = p.figure(figsize=(3, 2))
        # and axes
        ax = p.axes()
        # add the lines
        ax.add_collection(lines)
        # set the x axis
        p.xlim(transect.cross_shore.min(), transect.cross_shore.max())
        # set the y axis (add a bit of room cause the wiggles go over a few years)
        p.ylim(t.min()-730,t.max()+730)
        for o in ax.axes.findobj(text.Text):
            o.set_size('xx-small')
        datelocator = matplotlib.dates.AutoDateLocator()
        dateformatter = matplotlib.dates.AutoDateFormatter(datelocator)
        ax.axes.yaxis.set_major_formatter(dateformatter)
        f = cStringIO.StringIO()

        p.savefig(f, **plotproperties)
    finally:
        pylablock.release()
    f.seek(0)
    #cleanup
    #p.clf()
    return f
    
