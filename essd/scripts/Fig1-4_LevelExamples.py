from pathlib import Path
import matplotlib.pyplot as plt
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


sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')  # white style with tick marks

examples = pd.read_csv(Path('maps', 'level_examples.csv')).set_index('rgi_id')

glaciers = gpd.GeoDataFrame(pd.concat(
    [gpd.read_file(Path('rgi', f"RGI2000-v7.0-G-{reg}", f"RGI2000-v7.0-G-{reg}.shp")) for reg in examples.region.unique()],
    ignore_index=True))
glaciers = glaciers.loc[glaciers['rgi_id'].isin(examples.index)].set_index('rgi_id')

termini = glaciers.copy()
termini['geometry'] = gpd.points_from_xy(glaciers.termlon, glaciers.termlat, crs='epsg:4326')

lakes = gpd.read_file(Path('maps', 'lake_outlines.gpkg'))

for num, level in enumerate([1, 2, 3, 0]):
    fig, axs = plt.subplots(2, 2, figsize=(10, 10))

    this_level = examples.loc[examples['level'] == level].index
    axdict = dict(zip(this_level, axs.flatten()))

    for glac, row in examples.loc[examples['level'] == level].iterrows():
        fn_img = examples.loc[glac, 'image_id']

        img = gu.Raster(Path('maps', fn_img + '_pan.tif'))

        glacier = glaciers.to_crs(img.crs).loc[glac, :]
        term = termini.to_crs(img.crs).loc[glac, :]
        these_lakes = lakes.to_crs(img.crs).loc[lakes['rgi_id'] == glac]
        if len(these_lakes) > 0:
            cx, cy = these_lakes.union_all().envelope.centroid.x, these_lakes.union_all().envelope.centroid.y
            minx, miny, maxx, maxy = these_lakes.union_all().bounds

            # use the larger of the envelope of all the lakes, or 2 km
            scale = max(2000, max(maxx - minx, maxy - miny))
        else:
            cx, cy = term.geometry.x, term.geometry.y

            # use the larger of the square root of the area of the glacier, or 2 km
            scale = 1000 * max(2, np.floor(pow(glacier.area_km2, 0.5)))

        img.crop(crop_geom=[cx - 0.75 * scale, cy - 0.75 * scale,
                            cx + 0.75 * scale, cy + 0.75 * scale], inplace=True)
        xmin, ymin, xmax, ymax = img.bounds

        stretched = stretch_img(img, [0.008, 0.017, 0.031], [0.75, 0.50, 0.53])
        stretched.plot(ax=axdict[glac], add_cbar=False)

        # plot the glacier outline
        gpd.GeoDataFrame([glacier]).boundary.plot(ax=axdict[glac], color='#ff00f0')

        # plot the lake outlines, if they exist
        if len(these_lakes) > 0:
            these_lakes.boundary.plot(ax=axdict[glac], color='#00d8ff')

        axdict[glac].set_xlim(xmin, xmax)
        axdict[glac].set_ylim(ymin, ymax)

        axdict[glac].set_xticks([])
        axdict[glac].set_yticks([])


    ax1, ax2, ax3, ax4 = axs.flatten()

    label_loc = (0.03, 0.92)
    bbox = dict(fc="w")
    for lab, ax in zip('abcd', axs.flatten()):
        ax.annotate(f"{lab})", label_loc, xycoords='axes fraction', bbox=bbox)

    plt.subplots_adjust(hspace=0.05, wspace=0.05)

    fig.savefig(Path('figures', f"Fig{num+1}_Level_{level}_Examples.png"), bbox_inches='tight', dpi=400)
