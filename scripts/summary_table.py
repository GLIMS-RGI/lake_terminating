from pathlib import Path
from glob import glob
import pandas as pd
import geopandas as gpd


region_csvs = sorted(glob('*lakeflag.csv', root_dir='tables'))

regions = []
names = []
totals = []
level0 = []
level1 = []
level2 = []
level3 = []
level99 = []

for fn_csv in region_csvs:
    region, name = fn_csv.split('RGI2000-v7.0-G-')[1].split('_lakeflag')[0].split('_', maxsplit=1)

    region_csv = pd.read_csv(Path('tables', fn_csv))
    region_csv = pd.read_csv(fn_csv)
    
    regions.append(int(region))
    names.append(' '.join(name.split('_')).title())
    totals.append(len(region_csv))
    
    counts = region_csv['lake_level'].value_counts()
    level0.append(counts.loc[0])
    level1.append(counts.loc[1])
    level2.append(counts.loc[2])
    level3.append(counts.loc[3])
    
    if 99 in counts.index:
        level99.append(counts.loc[99])
    else:
        level99.append(0)


global_counts = pd.DataFrame(data={'region': regions, 'name': names, 'numglac': totals, 
                                   'level 0': level0, 'level 1': level1, 'level 2': level2, 
                                   'level 3': level3, 'level99': level99})

global_counts.set_index('region', inplace=True)
total = global_counts.sum(numeric_only=True)
total['name'] = ''

global_counts.loc['global'] = total

global_counts.to_csv(Path('tables', 'regional_summary.csv'))

