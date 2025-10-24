from pathlib import Path
from glob import glob
from tqdm import tqdm
import pandas as pd
import geopandas as gpd
import tools


# get a list of the table values
region_csvs = sorted(glob('*lakeflag.csv', root_dir='dataset/csv/'))

# iterate through csv for each region, create two additional datasets:
#   - dataset/lakeflags/{region}_lakeflag.gpkg, with the lakeflag CSV joined to the RGI7 centroid (all glaciers)
#   - dataset/outlines/{region}_laketerminating.gpkg, with outlines for only category 1-3.
for fn_csv in tqdm(region_csvs):
    region, name = fn_csv.split('RGI2000-v7.0-G-')[1].split('_lakeflag')[0].split('_', maxsplit=1)

    lakeflags = pd.read_csv(Path('dataset', 'csv', fn_csv))

    outlines = gpd.read_file(tools.rgi_loader('rgi', fn_csv.split('_lakeflag')[0]))

    centroids = outlines.copy()
    centroids['geometry'] = gpd.points_from_xy(centroids.cenlon, centroids.cenlat, crs='epsg:4326')

    merged = lakeflags.merge(centroids[['rgi_id', 'geometry']], on='rgi_id')
    gpd.GeoDataFrame(merged).to_file(Path('dataset', 'lakeflags', fn_csv.replace('.csv', '.gpkg')))

    merged = lakeflags.merge(outlines[['rgi_id', 'geometry']], on='rgi_id')
    gpd.GeoDataFrame(merged.loc[merged['lake_cat'].isin([1, 2, 3])]).to_file(
        Path('dataset', 'outlines', fn_csv.replace('lakeflag.csv', 'laketerminating.gpkg'))
    )
