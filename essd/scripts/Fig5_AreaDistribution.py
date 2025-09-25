from pathlib import Path
import numpy as np
import geopandas as gpd
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


base_url = Path('..', 'dataset', 'csv')

regions = ['01_alaska', '02_western_canada_usa', '03_arctic_canada_north', '04_arctic_canada_south',
           '05_greenland_periphery', '06_iceland', '07_svalbard_jan_mayen', '08_scandinavia', '09_russian_arctic',
           '10_north_asia', '11_central_europe', '12_caucasus_middle_east', '13_central_asia', '14_south_asia_west',
           '15_south_asia_east', '16_low_latitudes', '17_southern_andes', '18_new_zealand',
           '19_subantarctic_antarctic_islands']

names = ['Alaska', 'Western Canada and USA', 'Arctic Canada North', 'Arctic Canada South', 'Greenland Periphery',
         'Iceland', 'Svalbard and Jan Mayen', 'Scandinavia', 'Russian Arctic', 'North Asia', 'Central Europe',
         'Caucasus and Middle East', 'Central Asia', 'South Asia West', 'South Asia East', 'Low Latitudes',
         'Southern Andes', 'New Zealand', 'Subantarctic and Antarctic Islands']

lake_flags = []
areas = []

for reg in regions:
    lake_flags.append(pd.read_csv(Path(base_url, f"RGI2000-v7.0-G-{reg}_lakeflag.csv")).set_index('rgi_id'))
    outlines = gpd.read_file(Path('rgi', 'RGI2000-v7.0-G-' + reg,
                                  'RGI2000-v7.0-G-' + reg + '.shp')).set_index('rgi_id')

    areas.append(outlines[['area_km2']])

lake_flags = pd.concat(lake_flags)
areas = pd.concat(areas)

lake_flags['area'] = areas['area_km2']

lake_flags.reset_index(inplace=True)
lake_flags['region'] = lake_flags['rgi_id'].str.split('-', expand=True)[3]

regional_vals = pd.DataFrame()
regional_vals['total_area'] = lake_flags.groupby('region')['area'].sum()
regional_vals['lake_area'] = lake_flags.loc[lake_flags['lake_cat'].isin([2, 3])].groupby('region')['area'].sum()
regional_vals['pct_area'] = 100 * regional_vals['lake_area'] / regional_vals['total_area']
regional_vals.index = names

bins = np.logspace(-2, 3, 100)

densities = dict()
densities['all'], _ = np.histogram(lake_flags['area'], bins)
densities['cat0'], _ = np.histogram(lake_flags.loc[lake_flags['lake_cat'].isin([0]), 'area'], bins)
densities['cat1'], _ = np.histogram(lake_flags.loc[lake_flags['lake_cat'].isin([1]), 'area'], bins)
densities['cat2'], _ = np.histogram(lake_flags.loc[lake_flags['lake_cat'].isin([2]), 'area'], bins)
densities['cat3'], _ = np.histogram(lake_flags.loc[lake_flags['lake_cat'].isin([3]), 'area'], bins)

for lev, dens in densities.items():
    densities[lev] = dens * 1.
    densities[lev][dens == 0] = np.nan

# turn the densities into fractions
fractions = densities.copy()

for lev, dens in fractions.items():
    fractions[lev] = dens / np.nansum(dens)

# now, plot the distributions
sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')  # white style with tick marks

# fig, axs = plt.subplots(2, 1, figsize=(12, 14))
fig = plt.figure(figsize=(12, 14))
axs = []

gs = GridSpec(2, 2, figure=fig)
axs.append(fig.add_subplot(gs[0, 0]))
axs.append(fig.add_subplot(gs[0, 1]))
axs.append(fig.add_subplot(gs[1, :]))

labels = {'all': 'All', 'cat0': 'Category 0', 'cat1': 'Category 1',
          'cat2': 'Category 2', 'cat3': 'Category 3'}

markers = ['o', 's', 'X', '^', 'D']
colors = ['#7a0177', '#a1dab4', '#41b6c4', '#2c7fb8', '#253494']

for data, ax in zip([densities, fractions], axs[:2]):
    for cat, vals, marker, col in zip(data.keys(), data.values(), markers, colors):
        ax.plot(bins[:-1], vals, marker=marker, color=col, label=labels[cat], linewidth=2)
    ax.set_xscale('log')
    ax.set_yscale('log')

axs[1].legend(fontsize='small', loc='lower left')

axs[0].set_xlabel('Glacier Area (km$^2$, logscale)')
axs[0].set_ylabel('Number of Glaciers (logscale)')

axs[1].set_xlabel('Glacier Area (km$^2$, logscale)')
axs[1].set_ylabel('Fraction of Glaciers (logscale)')

axs[2] = sns.barplot(data=regional_vals['pct_area'], ax=axs[2], color='0.5')
axs[2].set_xticks(axs[2].get_xticks(), axs[2].get_xticklabels(), rotation=45, va='top', ha='right', size='x-small')
axs[2].bar_label(axs[2].containers[0], labels=regional_vals['lake_area'].astype(int), fontsize='xx-small')

axs[2].set_ylabel('Lake-terminating glacier area (%)')

label_locs = zip([0.01, 0.01, 0.005], 3 * [0.95])
for lab, loc, ax in zip('abc', label_locs, axs):
    ax.annotate(f"({lab})", loc, xycoords='axes fraction')

plt.tight_layout()

fig.savefig('figures/Fig5_AreaDistribution.png', bbox_inches='tight', dpi=300)
