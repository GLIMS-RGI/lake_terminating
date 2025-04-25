from pathlib import Path
import numpy as np
import geopandas as gpd
import pandas as pd
import seaborn as sns
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from matplotlib.colors import LogNorm


def convert_hexbin(hexbin):
    verts = hexbin.get_paths()[0].vertices
    polys = []

    for xo, yo in hexbin.get_offsets():
        xx = verts[:, 0] + xo
        yy = verts[:, 1] + yo
        polys.append(Polygon(zip(xx, yy)))

    return polys


def get_hex_gdf(glacs):
    extent = (-180., 180., -90., 90.)
    counts = plt.hexbin(glacs['cenlon'], glacs['cenlat'], gridsize=(36, 18), extent=extent)

    plt.close('all')

    bins = convert_hexbin(counts)

    hex_gdf = gpd.GeoDataFrame({'geometry': bins, 'count': counts.get_array()}, crs='epsg:4326')
    hex_gdf.loc[hex_gdf['count'] == 0] = np.nan

    return hex_gdf.dropna(subset=['count'])


base_url = 'https://github.com/GLIMS-RGI/lake_terminating/raw/refs/heads/main/tables/RGI2000-v7.0-G-'

regions = ['01_alaska', '02_western_canada_usa', '03_arctic_canada_north', '04_arctic_canada_south',
           '05_greenland_periphery', '06_iceland', '07_svalbard_jan_mayen', '08_scandinavia', '09_russian_arctic',
           '10_north_asia', '11_central_europe', '12_caucasus_middle_east', '13_central_asia', '14_south_asia_west',
           '15_south_asia_east', '16_low_latitudes', '17_southern_andes', '18_new_zealand',
           '19_subantarctic_antarctic_islands']

o1regions = gpd.read_file(Path('rgi', 'RGI2000-v7.0-regions', 'RGI2000-v7.0-o1regions.shp'))

lake_flags = []
coords = []

for reg in regions:
    lake_flags.append(pd.read_csv(base_url + reg + '_lakeflag.csv').set_index('rgi_id'))
    outlines = gpd.read_file(Path('rgi', 'RGI2000-v7.0-G-' + reg,
                                  'RGI2000-v7.0-G-' + reg + '.shp')).set_index('rgi_id')

    coords.append(outlines[['cenlon', 'cenlat', 'area_km2']])

lake_flags = pd.concat(lake_flags)

coords = pd.concat(coords)
coords['geometry'] = gpd.points_from_xy(coords['cenlon'], coords['cenlat'], crs='epsg:4326')
coords = gpd.GeoDataFrame(coords)

lake_flags = lake_flags.loc[lake_flags['lake_level'].isin([1, 2])].join(coords)
lake_flags = gpd.GeoDataFrame(lake_flags)

binned = get_hex_gdf(coords)
binned['area'] = binned.sjoin(coords).groupby(level=0)['area_km2'].sum()

binned['lake_count'] = binned.sjoin(lake_flags).groupby(level=0)['count'].count()
binned['lake_area'] = binned.sjoin(lake_flags).groupby(level=0)['area_km2'].sum()

binned['pct_count'] = binned['lake_count'] / binned['count'] * 100
binned['pct_area'] = binned['lake_area'] / binned['area'] * 100

# add na values for bins with no lakes

names = ['count', 'area', 'pct_count', 'pct_area']
labels = ['Number of Glaciers', 'Total Area (km$^2$)', 'Lake-terminating (%)', 'Lake-terminating Area (%)']

# set up the figure
sns.set_theme(font_scale=1.5, style="white", palette='colorblind')

fig, axs = plt.subplots(nrows=2, ncols=2, figsize=(22, 10), layout='constrained',
                        subplot_kw={'projection': ccrs.PlateCarree()})

for ax, name, lab, norm in zip(axs.flatten(), names, labels, [True, True, False, False]):
    ax.coastlines(linewidth=0.4)
    o1regions.boundary.plot(color='k', ax=ax, linewidth=0.8)

    if norm:
        _min, _max = max(binned[name].min(), 1), binned[name].max()

        binned.plot(name, ax=ax, legend=True, legend_kwds={'label': lab, 'pad': 0.01},
                    norm=LogNorm(vmin=_min, vmax=_max), zorder=10, alpha=0.6, ec='k')
    else:
        binned.plot(name, ax=ax, legend=True, legend_kwds={'label': lab, 'pad': 0.01},
                    zorder=10, alpha=0.8, ec='k')

    # if we have nans in this dataset, plot the empty boundaries
    if binned[name].isna().any():
        binned.loc[binned[name].isna()].boundary.plot(color='k', linewidth=0.4, ax=ax)

label_loc = (0.005, 0.95)
for lab, ax in zip('abcd', axs.flatten()):
    ax.annotate(f"({lab})", label_loc, xycoords='axes fraction')

fig.savefig(Path('figures', 'Fig6_GlobalDistribution.png'), bbox_inches='tight', dpi=300)
