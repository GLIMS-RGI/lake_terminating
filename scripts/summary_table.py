from pathlib import Path
from glob import glob
import pandas as pd
import geopandas as gpd
import tools


region_csvs = sorted(glob('*lakeflag.csv', root_dir='tables'))

levels = [0, 1, 2, 3, 98, 99]

regions = []
names = []
totals = []

level_dict = {'level0': [], 'level0area': [],
              'level1': [], 'level1area': [],
              'level2': [], 'level2area': [],
              'level3': [], 'level3area': [],
              'level98': [], 'level98area': [],
              'level99': [], 'level99area': []}

for fn_csv in region_csvs:
    region, name = fn_csv.split('RGI2000-v7.0-G-')[1].split('_lakeflag')[0].split('_', maxsplit=1)

    lakeflags = pd.read_csv(Path('tables', fn_csv))
    outlines = gpd.read_file(tools.rgi_loader('rgi', fn_csv.split('_lakeflag')[0]))

    lakeflags = lakeflags.merge(outlines[['rgi_id', 'area_km2']], left_on='rgi_id', right_on='rgi_id')

    regions.append(int(region))
    names.append(' '.join(name.split('_')).title())
    totals.append(len(lakeflags))
    
    counts = lakeflags['lake_level'].value_counts()
    for level in levels:
        if level in counts.index:
            area = lakeflags.loc[lakeflags['lake_level'] == level, 'area_km2'].sum()

            level_dict[f"level{level}"].append(counts.loc[level])
            level_dict[f"level{level}area"].append(area)
        else:
            level_dict[f"level{level}"].append(0)
            level_dict[f"level{level}area"].append(0)
    
global_counts = pd.DataFrame(data={'region': regions, 'name': names, 'numglac': totals} | level_dict)

global_counts.set_index('region', inplace=True)
total = global_counts.sum(numeric_only=True)
total['name'] = ''

global_counts.loc['global'] = total

count_cols = ['numglac'] + [f"level{level}" for level in levels]
global_counts[count_cols] = global_counts[count_cols].astype(int)

global_counts.to_csv(Path('tables', 'regional_summary.csv'))
