from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import patches, collections
import numpy as np
import pandas as pd
import geopandas as gpd
import geoutils as gu
import seaborn as sns


def stretch_img(img, vmin, vmax):
    stretch = img.copy()
    for vn, vx, b in zip(vmin, vmax, range(img.shape[0])):
        stretch[b][stretch[b] < vn] = vn
        stretch[b][stretch[b] > vx] = vx
        stretch[b] = (stretch[b] - vn) / (vx - vn)

    return stretch

def add_bbox(ax, bar, ann):
    left, right = ann

    bbox_left = ax.transData.inverted().transform(left.get_window_extent())
    bbox_right = ax.transData.inverted().transform(right.get_window_extent())

    text_bot = min(bbox_left[:, 1].tolist() + bbox_right[:, 1].tolist())
    bar_top = bar.xy[1] + bar.get_height()

    text_left = min(bbox_left[:, 0])
    text_right = max(bbox_right[:, 0])

    width = text_right - text_left
    height = bar_top - text_bot

    bbox = patches.Rectangle((text_left - 0.05 * width, text_bot - 0.05 * height), 1.1*width, 1.3*height,
                             facecolor='w', edgecolor='k', alpha=0.9, capstyle='round', zorder=2.5)

    return bbox


def add_scalebar(ax):
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()

    xscale = xmax - xmin
    yscale = ymax - ymin

    sb_length = max(np.floor(0.2 * xscale / 1000), 1) * 1000

    sbx = xmin + xscale * 0.08
    sby = ymin + yscale * 0.08

    hfact = 0.01 # 1% of the axis extent
    pad = 0.4

    # create the background box
    left = ax.text(sbx, sby - 0.01 * yscale, '0 km',
                   va='top', ha='center', size=10, color='k', zorder=2.5)
    right = ax.text(sbx + sb_length, sby - 0.01 * yscale, f"{int(sb_length / 1000)} km",
                    va='top', ha='center', size=10, color='k', zorder=2.5)

    full_bar = patches.Rectangle((sbx, sby), sb_length, hfact * yscale, color='k')
    half_bar = patches.Rectangle((sbx + 0.5 * sb_length, sby + pad/2 * hfact * yscale),
                                 0.495 * sb_length, (1-pad) * hfact * yscale, facecolor='w', edgecolor='none')

    bbox = add_bbox(ax, full_bar, (left, right))
    scalebar = collections.PatchCollection([bbox, full_bar, half_bar], match_original=True, zorder=2.5)
    ax.add_collection(scalebar)

    left.set_zorder(10)
    right.set_zorder(10)


sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')  # white style with tick marks

examples = pd.read_csv(Path('maps', 'category_examples.csv')).set_index('rgi_id')

glaciers = gpd.GeoDataFrame(pd.concat(
    [gpd.read_file(Path('rgi', f"RGI2000-v7.0-G-{reg}", f"RGI2000-v7.0-G-{reg}.shp")) for reg in examples.region.unique()],
    ignore_index=True))
glaciers = glaciers.loc[glaciers['rgi_id'].isin(examples.index)].set_index('rgi_id')

termini = glaciers.copy()
termini['geometry'] = gpd.points_from_xy(glaciers.termlon, glaciers.termlat, crs='epsg:4326')

lakes = gpd.read_file(Path('maps', 'lake_outlines.gpkg'))

for num, level in enumerate([3, 2, 1, 0]):
    fig, axs = plt.subplots(2, 2, figsize=(10, 10))

    this_level = examples.loc[examples['category'] == level].index
    axdict = dict(zip(this_level, axs.flatten()))

    for glac, row in examples.loc[examples['category'] == level].iterrows():
        fn_img = examples.loc[glac, 'image_id']

        img = gu.Raster(Path('maps', fn_img + '_pan_swir.tif'))

        glacier = glaciers.to_crs(img.crs).loc[glac, :]
        term = termini.to_crs(img.crs).loc[glac, :]
        these_lakes = lakes.to_crs(img.crs).loc[lakes['rgi_id'] == glac]
        if len(these_lakes) > 0:
            geom = gpd.GeoSeries(these_lakes['geometry'].to_list() + [term['geometry']]).union_all()
            cx, cy = geom.envelope.centroid.x, geom.envelope.centroid.y
            minx, miny, maxx, maxy = geom.bounds

            # use the larger of the envelope of all the lakes, or 2 km
            scale = max(2000, max(maxx - minx, maxy - miny))
        else:
            cx, cy = term.geometry.x, term.geometry.y

            # use the larger of the square root of the area of the glacier, or 2 km
            scale = 1000 * max(2, np.floor(pow(glacier.area_km2, 0.5)))

        img.crop(crop_geom=[cx - 0.75 * scale, cy - 0.75 * scale,
                            cx + 0.75 * scale, cy + 0.75 * scale], inplace=True)
        xmin, ymin, xmax, ymax = img.bounds

        vmins = [0.003, 0.05, 0.024]
        vmaxs = [0.223, 0.356, 0.307]

        stretched = stretch_img(img, vmins, vmaxs)
        stretched.plot(ax=axdict[glac], add_cbar=False)

        add_scalebar(axdict[glac])

        # plot the glacier outline
        gpd.GeoDataFrame([glacier]).boundary.plot(ax=axdict[glac], color='#d2042d', linewidth=2)

        # plot the lake outlines, if they exist
        if len(these_lakes) > 0:
            these_lakes.boundary.plot(ax=axdict[glac], color='#ffffff')

        axdict[glac].set_xlim(xmin, xmax)
        axdict[glac].set_ylim(ymin, ymax)

        axdict[glac].set_xticks([])
        axdict[glac].set_yticks([])

    ax1, ax2, ax3, ax4 = axs.flatten()

    label_loc = (0.03, 0.92)
    bbox = dict(fc="w", alpha=0.9)
    for lab, ax in zip('abcd', axs.flatten()):
        ax.annotate(f"({lab})", label_loc, xycoords='axes fraction', bbox=bbox)

    plt.subplots_adjust(hspace=0.05, wspace=0.05)

    fig.savefig(Path('figures', f"Fig{num+1}_Category_{level}_Examples.png"), bbox_inches='tight', dpi=400)
