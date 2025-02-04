from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import squarify


# load the regional summary from github
csv_url = 'https://raw.githubusercontent.com/GLIMS-RGI/lake_terminating/refs/heads/main/tables/regional_summary.csv'
data = pd.read_csv(csv_url)
data = data.loc[data['region'] != 'global']

# copy the region info and total number of glaciers
fig_data = pd.DataFrame(data=data[['region', 'name', 'numglac']])

# zero pad the region number
fig_data['region'] = fig_data['region'].str.pad(2, fillchar='0')

# get the total area for each region
fig_data['area'] = data[[c for c in data.columns if 'area' in c]].sum(axis=1)

# differentiate between lake-terminating (level 1, 2) and not lake-terminating (0, 3, 98, 99)
is_lake = [1, 2]
not_lake = [0, 3, 98, 99]

# calculate the number and area of lake-terminating and not lake-terminating glaciers for each region
fig_data['lake_num'] = data[[f"level{ii}" for ii in is_lake]].sum(axis=1)
fig_data['lake_area'] = data[[f"level{ii}area" for ii in is_lake]].sum(axis=1)

fig_data['not_lake_num'] = data[[f"level{ii}" for ii in not_lake]].sum(axis=1)
fig_data['not_lake_area'] = data[[f"level{ii}area" for ii in not_lake]].sum(axis=1)

# split off small regions by number, area:
thresh = 0.02 # cutoff of 2% of global total of lake-terminating glaciers

small_regs = fig_data.loc[fig_data['lake_num'] / fig_data['lake_num'].sum() < thresh]
fig_data.drop(small_regs.index, inplace=True)
fig_data.set_index('region', inplace=True)

# add the combined small regions back to the table
fig_data.loc['All others'] = small_regs.sum(numeric_only=True)

# get a list of colors
colors = matplotlib.cm.tab20b(np.linspace(0, 1, len(fig_data)))

# make the plot
sns.set_theme(font_scale=1.5, style="white")
sns.set_style('ticks')  # white style with tick marks

fig, axs = plt.subplots(1, 2, figsize=(18, 8))

for ax, name in zip(axs, ['num', 'area']):
    squarify.plot(ax=ax, sizes=fig_data[f"lake_{name}"], label=fig_data.index,
                  color=colors, text_kwargs=dict(size=12, color='w'))
    ax.axis('off')

    pcts = fig_data[f"lake_{name}"] / fig_data[f"lake_{name}"].sum()
    pcts[pcts < 0.02] = np.nan
    pct_labels = pd.Series([f"{p:.1%}" for p in pcts], index=pcts.index)
    pct_labels[pcts.isna()] = ''

    texts = [child for child in ax.get_children() if isinstance(child, matplotlib.text.Text)]
    annotations = [t for t in texts if t.get_text() in fig_data.index]

    for ii, ann in enumerate(annotations):
        if pct_labels.iloc[ii] != '':
            x, y = ann.get_position()
            ax.text(x, y, '\n' + pct_labels.iloc[ii], color='w', size=8, va='top', ha='center')

# annotate the panels
axs[0].annotate('a)', (0, 1.02), xycoords='axes fraction')
axs[1].annotate('b)', (0, 1.02), xycoords='axes fraction')

fig.savefig(Path('figures', 'Fig6_Treemap.png'), dpi=300, bbox_inches='tight')
