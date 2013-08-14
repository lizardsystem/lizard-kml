# -*- coding: utf-8 -*-
import logging

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates
import matplotlib.gridspec

logger = logging.getLogger(__name__)

# simplify for colors
typemap = {
    '': 'strand',
    'strandsuppletie': 'strand',
    'dijkverzwaring': 'duin',
    'strandsuppletie banket': 'strand',
    'duinverzwaring': 'duin',
    'strandsuppletie+vooroever': 'overig',
    'Duinverzwaring': 'duin',
    'duin': 'duin',
    'duinverzwaring en strandsuppleti': 'duin',
    'vooroever': 'vooroever',
    'zeewaartse duinverzwaring': 'duin',
    'banket': 'strand',
    'geulwand': 'geulwand',
    'anders': 'overig',
    'landwaartse duinverzwaring': 'duin',
    'depot': 'overig',
    'vooroeversuppletie': 'vooroever',
    'onderwatersuppletie': 'vooroever',
    'geulwandsuppletie': 'geulwand'
}
beachcolors = {
    'duin': 'peru',
    'strand': 'khaki',
    'vooroever': 'aquamarine',
    'geulwand': 'lightseagreen',
    'overig': 'grey'
}


def is_not_empty(array):
    """
    Test whether an numpy array is not empty.

    True if empty, False if not.

    """
    return (not np.isnan(array).all())


def is_empty(array):
    """
    Test whether an numpy array is empty.

    True if empty, False if not.

    """
    return np.isnan(array).all()


def combinedplot(dfs):
    """Create a combined plot of the coastal data"""

    shorelinedf = dfs['shorelinedf']
    transectdf = dfs['transectdf']
    nourishmentdf = dfs['nourishmentdf']
    mkldf = dfs['mkldf']
    bkldf = dfs['bkldf']
    bwdf = dfs['bwdf']
    dfdf = dfs['dfdf']
    dunefaildf = dfs['dunefaildf']

    transect = transectdf['transect'].irow(0)
    areaname = transectdf['areaname'].irow(0)

    # Plot the results.
    fig = plt.figure(figsize=(8, 9))
    # We define a grid of 5 areas
    gs = matplotlib.gridspec.GridSpec(5, 1, height_ratios=[5, 2, 2, 2, 2],
                                      right=0.71)
    gs.update(hspace=0.1)

    # Some common style properties, also store they style information file for
    # ggplot style in the directory where the script is.
    props = dict(linewidth=1, alpha=0.7, markeredgewidth=0, markersize=8,
                 linestyle='-', marker='.')
    date2num = matplotlib.dates.date2num


    #Figuur 1: momentane kustlijn / te toetsenkustlijn / basiskustlijn,
    # oftewel onderstaand tweede figuur. Bij voorkeur wel in het Nederlands en
    # volgens mij klopt de tekst bij de as nu niet (afstand tot RSP (meters))

    # The first axis contains the coastal indicators related to volume
    # Create the axis, based on the gridspec
    ax1 = fig.add_subplot(gs[0])
    # Set the main title
    ax1.set_title('Indicatoren van de toestand van de kust\ntransect %d (%s)'
                  % (transect, str(areaname).strip()))
    # Plot the three lines
    if (is_empty(mkldf['momentary_coastline']) and
            is_empty(bkldf['basal_coastline']) and
            is_empty(bkldf['testing_coastline']) ):
        # Hack: set first value to 0.0, to make sure the share x-axis is
        # generated properly for the other axes.
        len_basal_coastline = len(bkldf['basal_coastline'])
        if len_basal_coastline > 0:
            # set last element to 0.0
            bkldf['basal_coastline'][len_basal_coastline-1] = 0.0
    ax1.plot(date2num(mkldf['time_MKL']), mkldf['momentary_coastline'],
             label='momentane kustlijn', **props)
    ax1.plot(date2num(bkldf['time']), bkldf['basal_coastline'],
             label='basiskustlijn', **props)
    ax1.plot(date2num(bkldf['time']), bkldf['testing_coastline'],
             label='te toetsenkustlijn', **props)
    # Plot the legend. This uses the label
    ax1.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)
    # Hide the ticks for this axis (can't use set_visible on xaxis because it
    # is shared)
    try:
        for label in ax1.xaxis.get_ticklabels():
            label.set_visible(False)
    except ValueError:
        # No date set on axes, because of no data. No worries...
        pass
    # set y-label no matter what
    ax1.set_ylabel('Afstand [m]')


    # Figuur 2: duinvoet / hoogwater / laagwater, vanaf (ongeveer) 1848 voor
    # raai om de kilometer. Voor andere raaien vanaf 1965 (Jarkus)
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    if (is_not_empty(dfdf['dune_foot_upperMKL_cross']) or
            is_not_empty(dfdf['dune_foot_threeNAP_cross']) or
            is_not_empty(shorelinedf['mean_high_water']) or
            is_not_empty(shorelinedf['mean_low_water']) ):
        ax2.plot(date2num(shorelinedf['time']), shorelinedf['mean_low_water'],
                 label='Laagwater positie', **props)
        ax2.plot(date2num(shorelinedf['time']), shorelinedf['mean_high_water'],
                 label='Hoogwater positie', **props)
        ax2.plot(date2num(dfdf['time']), dfdf['dune_foot_upperMKL_cross'],
                 label='Duinvoet (BKL-schijf)', **props)
        ax2.plot(date2num(dfdf['time']), dfdf['dune_foot_threeNAP_cross'],
                 label='Duinvoet (NAP+3m)', **props)

        ax2.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)

        # Only show up to 5 major ticks on y-axis.
        ax2.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))

        # Again remove the xaxis labels
        try:
            for label in ax2.xaxis.get_ticklabels():
                label.set_visible(False)
        except ValueError:
            # No dates no problem
            pass
    # show y-label no matter what
    ax2.set_ylabel('Afstand [m]')


    # Figuur 3 strandbreedte bij hoogwater / strandbreedte bij laagwater (ook
    # vanaf ongeveer 1848 voor raai om de kilometer, voor andere raaien vanaf
    # 1965 )
    # Create another axis for the width and position parameters
    # Share the x axis with axes ax1
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    # Plot the 3 lines
    if (is_not_empty(bwdf['beach_width_at_MHW']) or
            is_not_empty(bwdf['beach_width_at_MLW'])):
        # !!! fill_between does not work with a datetime x (first element);
        # leaving as is for now
        # ax3.fill_between(np.asarray(bwdf['time']),
        #                  np.asarray(bwdf['beach_width_at_MLW']),
        #                  np.asarray(bwdf['beach_width_at_MHW']),
        #                  alpha=0.3,
        #                  color='black')
        ax3.plot(date2num(bwdf['time']), bwdf['beach_width_at_MLW'],
                 label='strandbreedte MLW', **props)
        ax3.plot(date2num(bwdf['time']), bwdf['beach_width_at_MHW'],
                 label='strandbreedte MHW', **props)

        # Only show 5 major ticks on y-axis
        ax3.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))
        ax3.yaxis.grid(False)
        # Again remove the xaxis labels
        try:
            for label in ax3.xaxis.get_ticklabels():
                label.set_visible(False)
        except ValueError:
            # No dates no problem
            pass
        # Place the legend
        ax3.legend(bbox_to_anchor=(1.01, 1), loc=2, borderaxespad=0.)
    # Dune foot is position but relative to RSP, so we can call it a width
    # show y-label no matter what
    ax3.set_ylabel('Breedte [m]')


    # Figuur 4 uitgevoerde suppleties, tekst bij de as bij voorkeur
    # Volume (m3/m)
    # Create the third axes, again sharing the x-axis
    ax4 = fig.add_subplot(gs[3], sharex=ax1)
    # Loop over eadge row, because we need to look up colors (bit of a hack)
    if len(nourishmentdf) > 0:
        # We need to store labels and a "proxy artist".
        proxies = []
        labels = []
        for i, row in nourishmentdf.iterrows():
            # Look up the color based on the type of nourishment
            try:
                color = beachcolors[typemap[row['type'].strip()]]
            except KeyError, e:
                logger.error("undefined beachcolor type: %s" % e)
                color = beachcolors['overig']
            # Strip spaces
            label = row['type'].strip()
            # Common properties
            ax4_props = dict(alpha=0.7, linewidth=2)
            # Plot a bar per nourishment
            ax4.fill_betweenx([0, row['volm']], date2num(row['beg_date']),
                              date2num(row['end_date']), edgecolor=color,
                              color=color, **ax4_props)
            if label not in labels:
                # Fill_between's are not added with labels.
                # So we'll create a proxy artist (a non plotted rectangle, with
                # the same color)
                # http://matplotlib.org/users/legend_guide.html
                proxy = matplotlib.patches.Rectangle((0, 0), 1, 1,
                                                     facecolor=color,
                                                     **ax4_props)
                proxy.set_label(label)
                proxies.append(proxy)
                labels.append(label)
        # Only show 5 major ticks on y-axis
        ax4.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))
        ax4.yaxis.grid(False)
        # Place the legend
        ax4.legend(proxies, labels, bbox_to_anchor=(1.01, 1), loc=2,
                   borderaxespad=0.)
        # Again remove the xaxis labels
        try:
            for label in ax4.xaxis.get_ticklabels():
                label.set_visible(False)
        except ValueError:
            # No dates no problem
            pass
    # show y-label anyway
    ax4.set_ylabel('Volume [m3/m]')


    # Figuur 5 Faalkans eerste duinrij (laatste figuur onderaan)
    # Sharing the x-axis
    ax5 = fig.add_subplot(gs[4], sharex=ax1)
    if is_not_empty(dunefaildf['probability_failure']):
        ax5.plot(date2num(dunefaildf['time']), dunefaildf['probability_failure'],
                 label='faalkans 1e duinrij', **props)
        # This one we want to see
        ax5.xaxis.set_visible(True)
        ax5.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5))
        ax5.yaxis.grid(False)
        ax5.set_yscale('log')
        # Now we plot the proxies with corresponding legends.
        ax5.legend(bbox_to_anchor=(1.01, 0), loc=3, borderaxespad=0.)
        ax5.set_xlabel('Tijd [jaren]')

    xlim = ax5.get_xlim()
    N = int(np.floor(np.diff(xlim) / 365 / 5))
    if N > 10:
        N = 10
    xaxis_locator = matplotlib.ticker.MaxNLocator(N)
    ax5.xaxis.set_major_locator(xaxis_locator)
    ax5.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y'))
    # show y-label no matter what
    ax5.set_ylabel('Kans [1/jr]')

    return fig


def all_else_fails_plot(dfs):
    """All else fails plot. Lots of checks are put in place already. Sometimes
    though, combined plot generation may result in a matplotlib.dates
    ValueError: ordinal must be >= 1. To show a figure anyway, this figure is
    shown.

    """
    transectdf = dfs['transectdf']

    transect = transectdf['transect'].irow(0)
    areaname = transectdf['areaname'].irow(0)

    fig = plt.figure(figsize=(7, 9))
    gs = matplotlib.gridspec.GridSpec(1, 1)
    gs.update(hspace=0.1)
    ax = fig.add_subplot(gs[0])
    ax.set_title('Onvoldoende data voor transect %d (%s) grafieken'
                  % (transect, str(areaname).strip()))
    return fig


def test_plot_ax1(dfs):
    shorelinedf = dfs['shorelinedf']
    transectdf = dfs['transectdf']
    nourishmentdf = dfs['nourishmentdf']
    mkldf = dfs['mkldf']
    bkldf = dfs['bkldf']
    bwdf = dfs['bwdf']
    dfdf = dfs['dfdf']
    dunefaildf = dfs['dunefaildf']

    transect = transectdf['transect'].irow(0)
    areaname = transectdf['areaname'].irow(0)

    # Plot the results.
    fig = plt.figure(figsize=(7, 9))
    # Some common style properties, also store they style information file for
    # ggplot style in the directory where the script is.
    props = dict(linewidth=1, alpha=0.7, markeredgewidth=0, markersize=8,
                 linestyle='-', marker='.')

    #Figuur 1: momentane kustlijn / te toetsenkustlijn / basiskustlijn,
    # oftewel onderstaand tweede figuur. Bij voorkeur wel in het Nederlands en
    # volgens mij klopt de tekst bij de as nu niet (afstand tot RSP (meters))

    # The first axis contains the coastal indicators related to volume
    # Create the axis, based on the gridspec

    ax1 = fig.add_subplot(111)
    # Set the main title
    ax1.set_title('Indicatoren van de toestand van de kust\ntransect %d (%s)'
                  % (transect, str(areaname).strip()))
    # Plot the three lines if there's at least one non-empty array
    if is_not_empty(mkldf['momentary_coastline']) or \
            is_not_empty(bkldf['basal_coastline']) or \
            is_not_empty(bkldf['testing_coastline']):
        date2num = matplotlib.dates.date2num
        ax1.plot(date2num(mkldf['time_MKL']), mkldf['momentary_coastline'],
                 label='momentane kustlijn', **props)
        ax1.plot(date2num(bkldf['time']), bkldf['basal_coastline'],
                 label='basiskustlijn', **props)
        ax1.plot(date2num(bkldf['time']), bkldf['testing_coastline'],
                 label='te toetsenkustlijn', **props)

        # Plot the legend. This uses the label
        ax1.legend(loc='upper left')
        # Hide the ticks for this axis (can't use set_visible on xaxis because it
        # is shared)
        try:
            for label in ax1.xaxis.get_ticklabels():
                label.set_visible(False)
        except ValueError:
            # No date set on axes, because of no data. No worries...
            pass
    # Show the y axis label
    ax1.set_ylabel('Afstand [m]')
    return fig


def test_plot_ax2(dfs):
    shorelinedf = dfs['shorelinedf']
    transectdf = dfs['transectdf']
    nourishmentdf = dfs['nourishmentdf']
    mkldf = dfs['mkldf']
    bkldf = dfs['bkldf']
    bwdf = dfs['bwdf']
    dfdf = dfs['dfdf']
    dunefaildf = dfs['dunefaildf']

    transect = transectdf['transect'].irow(0)
    areaname = transectdf['areaname'].irow(0)

    # Plot the results.
    fig = plt.figure(figsize=(7, 9))

    # Some common style properties, also store they style information file for
    # ggplot style in the directory where the script is.
    props = dict(linewidth=1, alpha=0.7, markeredgewidth=0, markersize=8,
                 linestyle='-', marker='.')
    date2num = matplotlib.dates.date2num
    # Figuur 2: duinvoet / hoogwater / laagwater, vanaf (ongeveer) 1848 voor
    # raai om de kilometer. Voor andere raaien vanaf 1965 (Jarkus)
    ax2 = fig.add_subplot(111)
    # Plot the four lines if at least is non-empty (= not all NaNs)
    if (is_not_empty(dfdf['dune_foot_upperMKL_cross']) or
            is_not_empty(dfdf['dune_foot_threeNAP_cross']) or
            is_not_empty(shorelinedf['mean_high_water']) or
            is_not_empty(shorelinedf['mean_low_water']) ):
        ax2.plot(date2num(dfdf['time']), dfdf['dune_foot_upperMKL_cross'],
                 label='Duinvoet (BKL-schijf)', **props)
        ax2.plot(date2num(dfdf['time']), dfdf['dune_foot_threeNAP_cross'],
                 label='Duinvoet (NAP+3 meter)', **props)
        ax2.plot(date2num(shorelinedf['time']), shorelinedf['mean_high_water'],
                 label='Hoogwater positie', **props)
        ax2.plot(date2num(shorelinedf['time']), shorelinedf['mean_low_water'],
                 label='Laagwater positie', **props)
        leg = ax2.legend(loc='best')
        leg.get_frame().set_alpha(0.7)

        # Look up the location of the tick labels, because we're removing all but
        # the first and last.
        locs = [ax2.yaxis.get_ticklocs()[0], ax2.yaxis.get_ticklocs()[-1]]
        # We don't want too much cluttering
        ax2.yaxis.set_ticks(locs)

        # Again remove the xaxis labels
        try:
            for label in ax2.xaxis.get_ticklabels():
                label.set_visible(False)
        except ValueError:
            # No dates no problem
            pass
    ax2.set_ylabel('Afstand [m]')
    return fig


def test_plot_ax3(dfs):
    shorelinedf = dfs['shorelinedf']
    transectdf = dfs['transectdf']
    nourishmentdf = dfs['nourishmentdf']
    mkldf = dfs['mkldf']
    bkldf = dfs['bkldf']
    bwdf = dfs['bwdf']
    dfdf = dfs['dfdf']
    dunefaildf = dfs['dunefaildf']

    transect = transectdf['transect'].irow(0)
    areaname = transectdf['areaname'].irow(0)

    # Plot the results.
    fig = plt.figure(figsize=(7, 9))

    # Some common style properties, also store they style information file for
    # ggplot style in the directory where the script is.
    props = dict(linewidth=1, alpha=0.7, markeredgewidth=0, markersize=8,
                 linestyle='-', marker='.')
    date2num = matplotlib.dates.date2num
    # Figuur 3 strandbreedte bij hoogwater / strandbreedte bij laagwater (ook
    # vanaf ongeveer 1848 voor raai om de kilometer, voor andere raaien vanaf
    # 1965 )
    # Create another axis for the width and position parameters
    # Share the x axis with axes ax1
    ax3 = fig.add_subplot(111)
    # Plot the 3 lines
    # !!! fill_between does not work with a datetime x (first element);
    # leaving as is for now
    # ax3.fill_between(np.asarray(bwdf['time']),
    #                  np.asarray(bwdf['beach_width_at_MLW']),
    #                  np.asarray(bwdf['beach_width_at_MHW']),
    #                  alpha=0.3,
    #                  color='black')
    if (is_not_empty(bwdf['beach_width_at_MHW']) or
            is_not_empty(bwdf['beach_width_at_MLW'])):
        ax3.plot(bwdf['time'], bwdf['beach_width_at_MHW'],
                 label='strandbreedte MHW', **props)
        ax3.plot(bwdf['time'], bwdf['beach_width_at_MLW'],
                 label='strandbreedte MLW', **props)
        # ax3.plot(date2num(dfdf['time']), dfdf['dune_foot_upperMKL_cross'],
        #          label='Duinvoet (BKL-schijf)', **props)
        # Dune foot is position but relative to RSP, so we can call it a width
        # Look up the location of the tick labels, because we're removing all but
        # the first and last.
        locs = [ax3.yaxis.get_ticklocs()[0], ax3.yaxis.get_ticklocs()[-1]]
        # We don't want too much cluttering
        ax3.yaxis.set_ticks(locs)
        ax3.yaxis.grid(False)
        # Again remove the xaxis labels
        try:
            for label in ax3.xaxis.get_ticklabels():
                label.set_visible(False)
        except ValueError:
            # No dates no problem
            pass
        # Place the legend
        ax3.legend(loc='upper left')
    ax3.set_ylabel('Breedte [m]')
    return fig


def test_plot_ax4(dfs):
    shorelinedf = dfs['shorelinedf']
    transectdf = dfs['transectdf']
    nourishmentdf = dfs['nourishmentdf']
    mkldf = dfs['mkldf']
    bkldf = dfs['bkldf']
    bwdf = dfs['bwdf']
    dfdf = dfs['dfdf']
    dunefaildf = dfs['dunefaildf']

    transect = transectdf['transect'].irow(0)
    areaname = transectdf['areaname'].irow(0)

    # Plot the results.
    fig = plt.figure(figsize=(7, 9))

    # Some common style properties, also store they style information file for
    # ggplot style in the directory where the script is.
    props = dict(linewidth=1, alpha=0.7, markeredgewidth=0, markersize=8,
                 linestyle='-', marker='.')
    # Figuur 4 uitgevoerde suppleties, tekst bij de as bij voorkeur
    # Volume (m3/m)
    # Create the third axes, again sharing the x-axis
    ax4 = fig.add_subplot(111)
    date2num = matplotlib.dates.date2num
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
        ax4_props = dict(alpha=0.7, linewidth=2)
        # Plot a bar per nourishment
        ax4.fill_betweenx([0, row['volm']], date2num(row['beg_date']),
                          date2num(row['end_date']), edgecolor=color,
                          color=color, **ax4_props)
        if label not in labels:
            # Fill_between's are not added with labels.
            # So we'll create a proxy artist (a non plotted rectangle, with
            # the same color)
            # http://matplotlib.org/users/legend_guide.html
            proxy = matplotlib.patches.Rectangle((0, 0), 1, 1,
                                                 facecolor=color, **ax4_props)
            proxy.set_label(label)
            proxies.append(proxy)
            labels.append(label)
    # Only use first and last tick label
    locs = [ax4.yaxis.get_ticklocs()[0], ax4.yaxis.get_ticklocs()[-1]]
    ax4.yaxis.set_ticks(locs)
    ax4.yaxis.grid(False)
    ax4.set_ylabel('Volume [m3/m]')
    # Again remove the xaxis labels
    try:
        for label in ax4.xaxis.get_ticklabels():
            label.set_visible(False)
    except ValueError:
        # No dates no problem
        pass
    # Place the legend
    ax4.legend(proxies, labels, loc='upper left')
    return fig


def test_plot_ax5(dfs):
    shorelinedf = dfs['shorelinedf']
    transectdf = dfs['transectdf']
    nourishmentdf = dfs['nourishmentdf']
    mkldf = dfs['mkldf']
    bkldf = dfs['bkldf']
    bwdf = dfs['bwdf']
    dfdf = dfs['dfdf']
    dunefaildf = dfs['dunefaildf']

    transect = transectdf['transect'].irow(0)
    areaname = transectdf['areaname'].irow(0)

    # Plot the results.
    fig = plt.figure(figsize=(7, 9))

    # Some common style properties, also store they style information file for
    # ggplot style in the directory where the script is.
    props = dict(linewidth=1, alpha=0.7, markeredgewidth=0, markersize=8,
                 linestyle='-', marker='.')
    date2num = matplotlib.dates.date2num
    # Figuur 5 Faalkans eerste duinrij (laatste figuur onderaan)
    # Sharing the x-axis
    ax5 = fig.add_subplot(111)
    if is_not_empty(dunefaildf['probability_failure']):
        ax5.plot(date2num(dunefaildf['time']),
                 dunefaildf['probability_failure'],
                 label='faalkans eerste duinrij', **props)
        # This one we want to see
        ax5.xaxis.set_visible(True)
        # Only use first and last tick label
        locs = [ax5.yaxis.get_ticklocs()[0], ax5.yaxis.get_ticklocs()[-1]]
        ax5.yaxis.set_ticks(locs)
        ax5.yaxis.grid(False)
        ax5.set_yscale('log')
        ax5.set_xlabel('Tijd [jaren]')
        # Show dates at decenia
        locator = matplotlib.dates.YearLocator(base=25)
        ax5.xaxis.set_major_locator(locator)
        ax5.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y'))
        # Now we plot the proxies with corresponding legends.
        ax5.legend(loc='best')
    ax5.set_ylabel('Kans [1/jr]')
    return fig


if __name__ == '__main__':
    print (
        'Be sure to run using [buildout_dir]/bin/python if you want'
        ' to test using the same libraries as the site'
    )
    try:
        from lizard_kml.jarkus.matplotlib_settings import \
            set_matplotlib_defaults
    except ImportError:
        # import locally anyway
        from matplotlib_settings import set_matplotlib_defaults

    set_matplotlib_defaults()

    try:
        from lizard_kml.jarkus.nc_models import makedfs
    except ImportError:
        # import locally anyway
        from nc_models import makedfs

    transects = [
        7005000,  # working
        7005475,  # no data for ax3 and ax4 figure (returns all-else-fails)
        9010047,  # has very few data (should also work)
        8008100,
    ]
    for transect in transects:
        dfs = makedfs(transect)
        try:
            fig1 = test_plot_ax1(dfs)
            fig1.savefig('nourishment-%s-ax1.png' % transect)
        except ValueError, e:
            print "ERROR - axis 1 for %s fails: %s" % (transect, e)
        try:
            fig2 = test_plot_ax2(dfs)
            fig2.savefig('nourishment-%s-ax2.png' % transect)
        except ValueError, e:
            print "ERROR - axis 2 for %s fails: %s" % (transect, e)
        try:
            fig3 = test_plot_ax3(dfs)
            fig3.savefig('nourishment-%s-ax3.png' % transect)
        except ValueError, e:
            print "ERROR - axis 3 for %s fails: %s" % (transect, e)
        try:
            fig4 = test_plot_ax4(dfs)
            fig4.savefig('nourishment-%s-ax4.png' % transect)
        except ValueError, e:
            print "ERROR - axis 4 for %s fails: %s" % (transect, e)
        try:
            fig5 = test_plot_ax5(dfs)
            fig5.savefig('nourishment-%s-ax5.png' % transect)
        except ValueError, e:
            print "ERROR - axis 5 for %s fails: %s" % (transect, e)
        try:
            fig_comb = combinedplot(dfs)
            fig_comb.savefig('nourishment-%s-combined.png' % transect)
        except ValueError, e:
            print("ERROR - combined for %s fails: %s. Saving 'all-else-fails'"
                  " (aef) plot." % (transect, e))
            all_else_fails_fig = all_else_fails_plot(dfs)
            all_else_fails_fig.savefig('nourishment-%s-aef.png' % transect)
