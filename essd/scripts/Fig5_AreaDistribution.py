from pathlib import Path
import numpy as np
import geopandas as gpd
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


base_url = 'https://github.com/GLIMS-RGI/lake_terminating/raw/refs/heads/main/tables/RGI2000-v7.0-G-'

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
    lake_flags.append(pd.read_csv(base_url + reg + '_lakeflag.csv').set_index('rgi_id'))
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
regional_vals['lake_area'] = lake_flags.loc[lake_flags['lake_level'].isin([1, 2])].groupby('region')['area'].sum()
regional_vals['pct_area'] = 100 * regional_vals['lake_area'] / regional_vals['total_area']
regional_vals.index = names

bins = np.logspace(-2, 3, 100)
dens_all, _ = np.histogram(lake_flags['area'], bins)
dens_lake, _ = np.histogram(lake_flags.loc[lake_flags['lake_level'].isin([1, 2]), 'area'], bins)

# now, plot the distributions
sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')  # white style with tick marks

fig, axs = plt.subplots(2, 1, figsize=(12, 14))

axs[0].plot(bins[:-1], dens_all, 'o-', color='#8da0cb', label='All', linewidth=2)
axs[0].plot(bins[:-1], dens_lake, 's-', color='#1f78b4', label='Lake-terminating', linewidth=2)

axs[0].set_xscale('log')
axs[0].set_yscale('log')
axs[0].legend(fontsize='small')

# now, set the labels
# axs[0].set_xticks(axs[0].get_xticks(), labels=[f"10$^{{{int(x)}}}$" for x in axs[0].get_xticks()])
# axs[0].set_xlim(-2.2, 4.2)

axs[0].set_xlabel('Glacier Area (km$^2$, logscale)')
axs[0].set_ylabel('Number of Glaciers (logscale)')

axs[1] = sns.barplot(data=regional_vals['pct_area'], ax=axs[1], color='0.5')
axs[1].set_xticks(axs[1].get_xticks(), axs[1].get_xticklabels(), rotation=45, va='top', ha='right', size='x-small')
axs[1].bar_label(axs[1].containers[0], labels=regional_vals['lake_area'].astype(int), fontsize='xx-small')

axs[1].set_ylabel('Lake-terminating glacier area (%)')

axs[0].annotate('a)', (0, 1.02), xycoords='axes fraction')
axs[1].annotate('b)', (0, 1.02), xycoords='axes fraction')

fig.savefig('figures/Fig5_AreaDistribution.png', bbox_inches='tight', dpi=300)
