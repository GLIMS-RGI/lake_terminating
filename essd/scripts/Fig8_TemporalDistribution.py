from pathlib import Path
import numpy as np
import geopandas as gpd
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


base_url = Path('..', 'dataset', 'csv')

regions = ['01_alaska', '02_western_canada_usa', '03_arctic_canada_north', '04_arctic_canada_south',
           '05_greenland_periphery', '06_iceland', '07_svalbard_jan_mayen', '08_scandinavia', '09_russian_arctic',
           '10_north_asia', '11_central_europe', '12_caucasus_middle_east', '13_central_asia', '14_south_asia_west',
           '15_south_asia_east', '16_low_latitudes', '17_southern_andes', '18_new_zealand',
           '19_subantarctic_antarctic_islands']

lake_flags = []
outlines = []

for reg in regions:
    lake_flags.append(pd.read_csv(Path(base_url, f"RGI2000-v7.0-G-{reg}_lakeflag.csv")).set_index('rgi_id'))
    outlines.append(gpd.read_file(Path('rgi', 'RGI2000-v7.0-G-' + reg,
                                  'RGI2000-v7.0-G-' + reg + '.shp')).set_index('rgi_id'))

lake_flags = pd.concat(lake_flags)
outlines = pd.concat(outlines)

outlines['src_date'] = pd.to_datetime(outlines['src_date'])
lake_flags['image_date'] = pd.to_datetime(lake_flags['image_date'], errors='coerce', format='%Y-%m-%d')

# how many outlines have the image date included?
ptag = np.count_nonzero(~lake_flags['image_date'].isna()) / len(outlines)

# make the plot
sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')  # white style with tick marks

bins = range(1990, 2021)

out_freq, _  = np.histogram(outlines['src_date'].dt.year, bins, density=True)
lake_freq, _ = np.histogram(lake_flags['image_date'].dt.year, bins, density=True)

out_freq = np.cumsum(out_freq)
lake_freq = np.cumsum(lake_freq)

fig, ax = plt.subplots(1, 1, figsize=(10, 6))
ax2 = ax.twinx()

ax.hist(outlines['src_date'].dt.year, bins, density=True, label='RGI7 Outline', color='#7a0177', alpha=0.6)
ax.hist(lake_flags['image_date'].dt.year, bins, density=True,
        #label=f"Lake Level ({100*ptag:.2f}%)", color='#1f78b4', alpha=0.6)
        label=f"Lake Level", color='#1f78b4', alpha=0.6)

ax2.step(np.array(bins[:-1]), out_freq, label='RGI7 Outline', color='#7a0177', lw=2)
ax2.step(np.array(bins[:-1]), lake_freq, label='RGI7 Outline', color='#1f78b4', lw=2)

ax.legend(loc='upper left')
ax.set_xlabel('Year')
ax.set_ylabel('Frequency')

ax2.set_ylim(0, 1.05)
ax2.set_ylabel('Cumulative Frequency')

fig.savefig(Path('figures', 'Fig8_TemporalDistribution.png'), dpi=200, bbox_inches='tight')

# now, print some statistics
rgi_mean = outlines['src_date'].dt.year.mean()
rgi_std = outlines['src_date'].dt.year.std()

lake_mean = lake_flags['image_date'].dt.year.mean()
lake_std = lake_flags['image_date'].dt.year.std()

print(f"RGI outline mean year (± 1 std dev): {int(rgi_mean)} ± {rgi_std:.1f}")
print(f"Lake classification mean year (± 1 std dev): {int(lake_mean)} ± {lake_std:.1f}")
