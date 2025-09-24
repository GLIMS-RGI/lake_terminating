from pathlib import Path
from glob import glob
import pandas as pd
import geopandas as gpd
import tools


region_csvs = sorted(glob('*lakeflag.csv', root_dir='tables'))

cats = [0, 1, 2, 3, 98, 99]

regions = []
names = []
totals = []

cat_dict = {'cat0': [], 'cat0area': [],
              'cat1': [], 'cat1area': [],
              'cat2': [], 'cat2area': [],
              'cat3': [], 'cat3area': [],
              'cat98': [], 'cat98area': [],
              'cat99': [], 'cat99area': []}

for fn_csv in region_csvs:
    region, name = fn_csv.split('RGI2000-v7.0-G-')[1].split('_lakeflag')[0].split('_', maxsplit=1)

    lakeflags = pd.read_csv(Path('tables', fn_csv))
    outlines = gpd.read_file(tools.rgi_loader('rgi', fn_csv.split('_lakeflag')[0]))

    lakeflags = lakeflags.merge(outlines[['rgi_id', 'area_km2']], left_on='rgi_id', right_on='rgi_id')

    regions.append(int(region))
    names.append(' '.join(name.split('_')).title())
    totals.append(len(lakeflags))
    
    counts = lakeflags['lake_cat'].value_counts()
    for cat in cats:
        if cat in counts.index:
            area = lakeflags.loc[lakeflags['lake_cat'] == cat, 'area_km2'].sum()

            cat_dict[f"cat{cat}"].append(counts.loc[cat])
            cat_dict[f"cat{cat}area"].append(area)
        else:
            cat_dict[f"cat{cat}"].append(0)
            cat_dict[f"cat{cat}area"].append(0)
    
global_counts = pd.DataFrame(data={'region': regions, 'name': names, 'numglac': totals} | cat_dict)

global_counts.set_index('region', inplace=True)
total = global_counts.sum(numeric_only=True)
total['name'] = ''

global_counts.loc['global'] = total

count_cols = ['numglac'] + [f"cat{cat}" for cat in cats]
global_counts[count_cols] = global_counts[count_cols].astype(int)

global_counts.to_csv(Path('tables', 'regional_summary.csv'))
