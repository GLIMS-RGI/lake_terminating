from pathlib import Path
from glob import glob
from tqdm import tqdm
import pandas as pd
import geopandas as gpd
import tools


def add_category(df):
    """
    Given a dataframe of lake-terminating glacier flags:

        - reverse the order of lake-terminating category so that 3 is the highest and 0 is the lowest;
        - re-name the 'lake_level' attribute to 'lake_cat'

    :param df: the dataframe of lake-terminating glacier flags
    :return: the dataframe, with the changes made
    """
    cols = list(df.columns)
    df['lake_cat'] = df['lake_level'].replace({1: 3, 3: 1})

    lev_ind = next(ind for ind, x in enumerate(cols) if x == 'lake_level')
    cols.insert(lev_ind, 'lake_cat')
    cols.remove('lake_level')

    return df[cols]


# get a list of the table values
region_csvs = sorted(glob('*lakeflag.csv', root_dir='tables'))

# iterate through each region, applying the changes to the category values
# also, create two additional datasets:
#   - {region}_lakeflag.gpkg, with the lakeflag CSV joined to the RGI7 centroid (all glaciers)
#   - {region}_laketerminating.gpkg, with outlines for only category 1-3.
for fn_csv in tqdm(region_csvs):
    region, name = fn_csv.split('RGI2000-v7.0-G-')[1].split('_lakeflag')[0].split('_', maxsplit=1)

    lakeflags = add_category(pd.read_csv(Path('tables', fn_csv)))

    outlines = gpd.read_file(tools.rgi_loader('rgi', fn_csv.split('_lakeflag')[0]))

    centroids = outlines.copy()
    centroids['geometry'] = gpd.points_from_xy(centroids.cenlon, centroids.cenlat, crs='epsg:4326')

    merged = lakeflags.merge(centroids[['rgi_id', 'geometry']], on='rgi_id')
    gpd.GeoDataFrame(merged).to_file(Path('tables', fn_csv.replace('.csv', '.gpkg')))

    merged = lakeflags.merge(outlines[['rgi_id', 'geometry']], on='rgi_id')
    gpd.GeoDataFrame(merged.loc[merged['lake_cat'].isin([1, 2, 3])]).to_file(
        Path('tables', fn_csv.replace('lakeflag.csv', 'laketerminating.gpkg'))
    )

    # do this last
    lakeflags.to_csv(Path('tables', fn_csv), index=False)
