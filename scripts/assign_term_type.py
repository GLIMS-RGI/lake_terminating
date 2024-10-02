from pathlib import Path
from glob import glob
import pandas as pd
import geopandas as gpd
import tools


regions = [fn.split('_lakeflag.csv')[0] for fn in sorted(glob('*lakeflag.csv', root_dir='tables'))]

for reg in regions:
    print(reg)
    failed = False

    lakeflags = pd.read_csv(Path('tables', reg + '_lakeflag.csv'))

    if 'term_type' in lakeflags:
        # term_type has already been added to the csv, so we can continue
        continue

    outlines = gpd.read_file(tools.rgi_loader('rgi', reg))
    lakeflags = lakeflags.merge(outlines[['rgi_id', 'term_type']], left_on='rgi_id', right_on='rgi_id')

    if len(lakeflags) != len(outlines):
        print(f"Sizes for {reg} differ.")
        failed = True

    if (~lakeflags['rgi_id'].isin(outlines['rgi_id'])).any():
        print(f"{reg} has at least one incorrect RGI ID.")
        lakeflags.loc[~lakeflags['rgi_id'].isin(outlines['rgi_id'])].to_csv(f"{reg}_incorrect_ids.csv", index=False)
        failed = True
        
    if (~outlines['rgi_id'].isin(outlines['rgi_id'])).any():
        print(f"{reg} has at least one missing glacier.")
        outlines.loc[~outlines['rgi_id'].isin(lakeflags['rgi_id']), 'rgi_id'].to_csv(f"{reg}_missing_ids.csv", index=False)
        failed = True

    # only finalize the csv if it has passed all checks
    if not failed:
        print(f"{reg} has passed all checks.")
        # only set the terminus type where it has not already been set
        not_set = lakeflags['term_type'] == 9

        # lake_level 1 or 2 is defined as lake-terminating
        is_lake = lakeflags['lake_level'].isin([1, 2])
        is_land = lakeflags['lake_level'].isin([0, 3])

        # some regions have mapped marine-terminating and shelf-terminating glaciers
        is_shelf = lakeflags['lake_level'] == 98
        is_marine = lakeflags['lake_level'] == 99

        lakeflags.loc[not_set & is_land, 'term_type'] = 0 # set land-terminating
        lakeflags.loc[not_set & is_marine, 'term_type'] = 1 # set marine-terminating
        lakeflags.loc[not_set & is_lake, 'term_type'] = 2 # set lake-terminating
        lakeflags.loc[not_set & is_shelf, 'term_type'] = 3 # set shelf-terminating

        lakeflags.to_csv(Path('tables', reg + '_lakeflag.csv'), index=False)

