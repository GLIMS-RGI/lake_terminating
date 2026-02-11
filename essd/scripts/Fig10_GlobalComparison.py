from pathlib import Path
from glob import glob
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.pyplot import title

sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')

# load the regional summary
summary = pd.read_csv(Path('..', 'dataset', 'regional_summary.csv'))
summary['lake_term'] = summary[['cat2', 'cat3']].sum(axis=1)

# drop the global row
summary.drop(19, inplace=True)

# create a dataframe from each regional csv
region_comparison = pd.read_csv(Path('comparison_data', 'global_comparison.csv'))

# change the region slightly for plotting, to give separation between inventories
region_comparison['region'] = region_comparison['region'].astype(float)
region_comparison.loc[region_comparison['inventory'] == 'shugar2020', 'region'] -= 0.2
region_comparison.loc[region_comparison['inventory'] == 'zhang2024', 'region'] += 0.2

# rename inventories for plotting
region_comparison['inventory'] = region_comparison['inventory'].replace({'shugar2020': 'Shugar et al., 2020',
                                                                         'zhang2024': 'Zhang et al., 2024',
                                                                         'song2025': 'Song et al., 2025'})

# color palette for inventory
scatter_palette = {'Shugar et al., 2020': '#a6cee3', 'Zhang et al., 2024': '#1f78b4', 'Song et al., 2025': '#b2df8a'}

# rename columns for plotting/legend
region_comparison.rename(columns={'inventory': 'Inventory', 'buffer': 'Buffer (m)'}, inplace=True)

# make the plot
fig, ax = plt.subplots(1, 1, figsize=(15, 5))

sns.scatterplot(data=region_comparison, x='region', y='nglac', hue='Inventory',
                style='Buffer (m)', ax=ax, palette=scatter_palette, s=64)

# show number of manually-identified lake-terminating glaciers for each region
ax.errorbar(summary.index+1, summary.lake_term, xerr=0.4, fmt='none', linewidth=2, ecolor='k', label='Manual')

ax.set_ylabel('Number of lake-terminating glaciers')
ax.set_xlabel('RGI Region')

# re-make the legend
h, l = ax.get_legend_handles_labels()

# split legend into two separate legends
inv_h = h[0:4] + [h[9]] # add manual to inventory handles
mark_h = h[4:9]

inv_l = l[0:4] + [l[9]] # add manual to inventory labels
mark_l = l[4:9]

# add the inventory and marker legend separately
inv_leg = ax.legend(inv_h, inv_l, fontsize=10, loc='lower left', frameon=True)
mark_leg = ax.legend(mark_h, mark_l, fontsize=10, loc='upper right', frameon=True)

# add the inventory legend as a separate artist
ax.add_artist(inv_leg)
ax.set_xticks(range(1, 20))
ax.set_yscale('log')

fig.savefig(Path('figures', 'Fig10_GlobalComparison.png'), bbox_inches='tight', dpi=200)
