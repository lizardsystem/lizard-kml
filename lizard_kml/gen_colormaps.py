import numpy as np
import matplotlib.pyplot as plt

if __name__ == '__main__':
    a = np.linspace(0, 1, 256).reshape(1,-1)
    a = np.vstack((a,a))

    # Get a list of the colormaps in matplotlib.  Ignore the ones that end with
    # '_r' because these are simply reversed versions of ones that don't end
    # with '_r'
    maps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
    nmaps = len(maps) + 1

    ARR = []

    fig = plt.figure(figsize=(6,3))
    fig.subplots_adjust(top=1, bottom=0, left=0, right=1)
    for i,m in enumerate(maps):
        ax = plt.subplot(nmaps/2, 2, i+1)
        plt.axis("off")
        plt.imshow(a, aspect='auto', cmap=plt.get_cmap(m), origin='lower')
        x0, y0, x1, y1 = ax.get_position().get_points().flatten()
        #x0, y0, x1, y1 = ax.get_window_extent().bounds
        l, t = ax.transData.transform_point([x0, y0])
        r, b = ax.transData.transform_point([x1, y1])
        #print '%i, %i' % (x, fig.bbox.height - y)
        #pos = x, fig.bbox.height - y
        #pos = int(np.floor(ax.get_position().ymax * HH))
        ARR.append((m, (int(l), int(fig.bbox.height - t))))
        #pos = list(ax.get_position().bounds)
        #fig.text(pos[0] - 0.01, pos[1], m, fontsize=10, horizontalalignment='right')

    import os
    if os.path.isdir("static"):
        fig.savefig("static/lizard_kml/color_maps.png",dpi=80,facecolor='gray')

    import pprint
    pprint.pprint(ARR)
