from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd
import geoutils as gu
import seaborn as sns
import map_tools


sns.set_theme(font_scale=1.8, style="white")
sns.set_style('ticks')  # white style with tick marks

examples = pd.read_csv(Path('maps', 'category_examples.csv')).set_index('rgi_id')

glaciers = gpd.GeoDataFrame(pd.concat(
    [gpd.read_file(Path('rgi', f"RGI2000-v7.0-G-{reg}", f"RGI2000-v7.0-G-{reg}.shp")) for reg in examples.region.unique()],
    ignore_index=True))
glaciers = glaciers.loc[glaciers['rgi_id'].isin(examples.index)].set_index('rgi_id')

termini = glaciers.copy()
termini['geometry'] = gpd.points_from_xy(glaciers.termlon, glaciers.termlat, crs='epsg:4326')

lakes = gpd.read_file(Path('maps', 'lake_outlines.gpkg'))

# bit of a kludge, but make the figure with 4 panels and remove 2 later
fig, axs = plt.subplots(2, 2, figsize=(10, 10))

this_level = examples.loc[examples['category'] == 'c'].index
axdict = dict(zip(this_level, axs.flatten()))

for glac, row in examples.loc[examples['category'] == 'c'].iterrows():
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

    stretched = map_tools.stretch_img(img, vmins, vmaxs)
    stretched.plot(ax=axdict[glac], add_cbar=False)

    map_tools.add_scalebar(axdict[glac])

    # plot the glacier outline
    gpd.GeoDataFrame([glacier]).boundary.plot(ax=axdict[glac], color='#d2042d', linewidth=2)

    # plot the lake outlines, if they exist
    if len(these_lakes) > 0:
        these_lakes.boundary.plot(ax=axdict[glac], color='#ffffff')

    axdict[glac].set_xlim(xmin, xmax)
    axdict[glac].set_ylim(ymin, ymax)

    axdict[glac].set_xticks([])
    axdict[glac].set_yticks([])

label_loc = (0.03, 0.92)
bbox = dict(fc="w", alpha=0.9)
for lab, ax in zip('ab', axs.flatten()):
    ax.annotate(f"({lab})", label_loc, xycoords='axes fraction', bbox=bbox)

plt.subplots_adjust(hspace=0.05, wspace=0.05)

# remove the bottom row of axes
_, _, ax3, ax4 = axs.flatten()
ax3.remove()
ax4.remove()

fig.savefig(Path('figures', f"Fig9_Conflicts.png"), bbox_inches='tight', dpi=400)
