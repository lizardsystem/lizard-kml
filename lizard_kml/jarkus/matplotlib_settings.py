import matplotlib as mpl

def set_matplotlib_defaults():
    # reset to matplotlibs internal defaults
    mpl.rcdefaults()
    # use in memory backend
    mpl.use('Agg')
    # Sans-serif looks best for plots
    mpl.rcParams['font.family'] = 'sans-serif'
    # Some modern fonts
    mpl.rcParams['font.sans-serif'] = 'Bitstream Vera Sans, Lucida Grande, Verdana, Geneva, Lucid, Arial, Helvetica, Avant Garde, sans-serif'
    
    # Other different from rcdefaults
    mpl.rcParams['patch.linewidth'] = 0.5
    mpl.rcParams['patch.facecolor'] = '#348ABD'
    mpl.rcParams['patch.edgecolor'] = '#eeeeee'
    mpl.rcParams['font.size'] = 10.0
    mpl.rcParams['font.sans-serif'] = 'Bitstream Vera Sans, Lucida Grande, Verdana, Geneva, Lucid, Arial, Helvetica, Avant Garde, sans-serif'
    mpl.rcParams['font.monospace'] = 'Andale Mono, Nimbus Mono L, Courier New, Courier, Fixed, Terminal, monospace'
    mpl.rcParams['axes.facecolor'] = '#eeeeee'
    mpl.rcParams['axes.edgecolor'] = '#bcbcbc'
    mpl.rcParams['axes.linewidth'] = 1
    mpl.rcParams['axes.grid'] = True
    mpl.rcParams['axes.titlesize'] = 'x-large'
    mpl.rcParams['axes.labelsize'] = 'large'
    mpl.rcParams['axes.labelcolor'] = '#555555'
    mpl.rcParams['axes.axisbelow'] = True
    mpl.rcParams['axes.color_cycle'] = '#348ABD, #7A68A6, #A60628, #467821, #CF4457, #188487, #E24A33'
    mpl.rcParams['xtick.major.size'] = 0
    mpl.rcParams['xtick.minor.size'] = 0
    mpl.rcParams['xtick.major.pad'] = 6
    mpl.rcParams['xtick.minor.pad'] = 6
    mpl.rcParams['xtick.color'] = '#555555'
    mpl.rcParams['ytick.major.size'] = 0
    mpl.rcParams['ytick.minor.size'] = 0
    mpl.rcParams['ytick.major.pad'] = 6
    mpl.rcParams['ytick.minor.pad'] = 6
    mpl.rcParams['ytick.color'] = '#555555'
    mpl.rcParams['legend.fancybox'] = True
    mpl.rcParams['figure.figsize'] = '11, 8'
    mpl.rcParams['figure.facecolor'] = '0.85'
    mpl.rcParams['figure.edgecolor'] = '0.50'
    mpl.rcParams['figure.subplot.hspace'] = 0.5
