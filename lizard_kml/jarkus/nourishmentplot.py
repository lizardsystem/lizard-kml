# -*- coding: utf-8 -*-

if __name__ == '__main__':
    print ('Be sure to run using [buildout_dir]/bin/python if you want'
    ' to test using the same libraries as the site')
    from lizard_kml.jarkus.matplotlib_settings import set_matplotlib_defaults
    set_matplotlib_defaults()

import bisect
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates 

import pandas
import statsmodels.api as sm
import netCDF4
import matplotlib.gridspec

from lizard_kml.jarkus.nc_models import makedfs

def combinedplot(dfs):
    """Create a combined plot of the coastal data"""
    
    shorelinedf = dfs['shorelinedf']
    transectdf = dfs['transectdf']
    nourishmentdf = dfs['nourishmentdf']
    mkldf = dfs['mkldf']
    bkldf = dfs['bkldf']
    bwdf = dfs['bwdf']
    dfdf = dfs['dfdf']

    transect = transectdf['transect'].irow(0)
    areaname = transectdf['areaname'].irow(0)
    
    # Plot the results.
    fig = plt.figure(figsize=(10,10))
    # We define a grid of 3 areas 
    gs = matplotlib.gridspec.GridSpec(4, 1, height_ratios=[5, 2, 2, 2]) 
    gs.update(hspace=0.1)
    
    # Some common style properties, also store they style information file for ggplot style in the directory where the script is.
    props = dict(linewidth=2, alpha=0.7, markeredgewidth=0, markersize=8, linestyle='-', marker='.')

    #Figuur 1: momentane kustlijn / te toetsenkustlijn / basiskustlijn, oftewel onderstaand tweede figuur. Bij voorkeur wel in het Nederlands en volgens mij klopt de tekst bij de as nu niet (afstand tot RSP (meters))
  
    # The first axis contains the coastal indicators related to volume
    # Create the axis, based on the gridspec

    ax1 = fig.add_subplot(gs[0])
    # Set the main title
    ax1.set_title('Kengetallen van de toestand van de kust\ntransect %d (%s)' % (transect, str(areaname).strip()))
    # Plot the three lines
    date2num = matplotlib.dates.date2num
    ax1.plot(date2num(mkldf['time_MKL']), mkldf['momentary_coastline'], label='momentane kustlijn', **props)
    ax1.plot(date2num(bkldf['time']), bkldf['basal_coastline'], label='basiskustlijn', **props)
    ax1.plot(date2num(bkldf['time']), bkldf['testing_coastline'], label='te toetsenkustlijn', **props)
    
    # Plot the legend. This uses the label
    ax1.legend(loc='upper left')
    # Show the y axis label
    ax1.set_ylabel('Afstand [m]')
    # Hide the ticks for this axis (can't use set_visible on xaxis because it is shared)
    try:
        for label in ax1.xaxis.get_ticklabels():
            label.set_visible(False)
    except ValueError, e:
        # No date set on axes, because of no data. No worries...
        pass

    
    # Figuur 2: duinvoet / hoogwater / laagwater, vanaf (ongeveer) 1848 voor raai om de kilometer. Voor andere raaien vanaf 1965 (Jarkus) 
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.plot(date2num(dfdf['time']), dfdf['dune_foot_rsp'], label='duinvoet positie', **props)
    ax2.plot(date2num(shorelinedf['time']), shorelinedf['dune_foot'], label='historische duinvoet positie', **props)
    ax2.plot(date2num(shorelinedf['time']), shorelinedf['mean_high_water'], label='historische hoogwater positie', **props)
    ax2.plot(date2num(shorelinedf['time']), shorelinedf['mean_high_water'], label='historische laagwater positie', **props)
    leg = ax2.legend(loc='best')
    leg.get_frame().set_alpha(0.7)

    # Look up the location of the tick labels, because we're removing all but the first and last.
    locs = [ax2.yaxis.get_ticklocs()[0], ax2.yaxis.get_ticklocs()[-1]]
    # We don't want too much cluttering
    ax2.yaxis.set_ticks(locs)
    
    # Again remove the xaxis labels
    try:
        for label in ax2.xaxis.get_ticklabels():
            label.set_visible(False)
    except ValueError, e:
        # No dates no problem
        pass
    ax2.set_ylabel('Afstand [m]') 
    
    # Figuur 3 strandbreedte bij hoogwater / strandbreedte bij laagwater (ook vanaf ongeveer 1848 voor raai om de kilometer, voor andere raaien vanaf 1965 )
    # Create another axis for the width and position parameters
    # Share the x axis with axes ax1
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    # Plot the 3 lines
    '''
    ax3.fill_between(np.asarray(bwdf['time']), np.asarray(bwdf['beach_width_at_MLW']), np.asarray(bwdf['beach_width_at_MHW']), alpha=0.3, color='black')
    ax3.plot(bwdf['time'], bwdf['beach_width_at_MHW'], label='strandbreedte MHW', **props)
    ax3.plot(bwdf['time'], bwdf['beach_width_at_MLW'], label='strandbreedte MLW', **props)
    '''
    ax3.plot(date2num(dfdf['time']), dfdf['dune_foot_rsp'], label='duinvoet positie', **props)
    # Dune foot is position but relative to RSP, so we can call it a width
    ax3.set_ylabel('Breedte [m]') 
    # Look up the location of the tick labels, because we're removing all but the first and last.
    locs = [ax3.yaxis.get_ticklocs()[0], ax3.yaxis.get_ticklocs()[-1]]
    # We don't want too much cluttering
    ax3.yaxis.set_ticks(locs)
    ax3.yaxis.grid(False)
    # Again remove the xaxis labels
    try:
        for label in ax3.xaxis.get_ticklabels():
            label.set_visible(False)
    except ValueError, e:
        # No dates no problem
        pass
    # Place the legend
    ax3.legend(loc='upper left')
    
    
    # Figuur 4 uitgevoerde suppleties (laatste figuure onderaan), tekst bij de as bij voorkeur Volume (m3/m)
    
    # Create the third axes, again sharing the x-axis
    ax4 = fig.add_subplot(gs[3],sharex=ax1)
    # We need to store labels and a "proxy artist". 
    proxies = []
    labels = []
    # Loop over eadge row, because we need to look up colors (bit of a hack)
    for i, row in nourishmentdf.iterrows():
        # Look up the color based on the type of nourishment
        color = beachcolors[typemap[row['type'].strip()]]
        # Strip spaces
        label = row['type'].strip()
        # Common properties
        props = dict(alpha=0.7, linewidth=2)
        # Plot a bar per nourishment
        ax4.fill_betweenx([0,row['volm']],date2num(row['beg_date']), date2num(row['end_date']), edgecolor=color, color=color, **props)
        if label not in labels:
            # Fill_between's are not added with labels. 
            # So we'll create a proxy artist (a non plotted rectangle, with the same color)
            # http://matplotlib.org/users/legend_guide.html
            proxy = matplotlib.patches.Rectangle((0, 0), 1, 1, facecolor=color, **props)
            proxy.set_label(label)
            proxies.append(proxy)
            labels.append(label)
    # Only use first and last tick label
    locs = [ax4.yaxis.get_ticklocs()[0], ax4.yaxis.get_ticklocs()[-1]]
    ax4.yaxis.set_ticks(locs)
    ax4.yaxis.grid(False)
    #ax3.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.0f'))
    ax4.set_ylabel('Volume [m3/m]')
    ax4.set_xlabel('Tijd [jaren]')
    # This one we want to see
    ax4.xaxis.set_visible(True)
    # Show dates at decenia
    locator = matplotlib.dates.YearLocator(base=25)
    ax4.xaxis.set_major_locator(locator)
    ax4.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y'))
    # Now we plot the proxies with corresponding legends.
    legend = ax4.legend(proxies, labels, loc='upper left')
    return fig

if __name__ == '__main__':
    transect = 7004200
    dfs = makedfs(transect)
    fig = combinedplot(dfs)
    fig.savefig('nourishment-7004200.png')
