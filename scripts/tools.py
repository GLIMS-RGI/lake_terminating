import os
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import geopandas as gpd


rgi_regions = ['RGI2000-v7.0-G-01_alaska',
    'RGI2000-v7.0-G-02_western_canada_usa',
    'RGI2000-v7.0-G-03_arctic_canada_north',
    'RGI2000-v7.0-G-04_arctic_canada_south',
    'RGI2000-v7.0-G-05_greenland_periphery',
    'RGI2000-v7.0-G-06_iceland',
    'RGI2000-v7.0-G-07_svalbard_jan_mayen',
    'RGI2000-v7.0-G-08_scandinavia',
    'RGI2000-v7.0-G-09_russian_arctic',
    'RGI2000-v7.0-G-10_north_asia',
    'RGI2000-v7.0-G-11_central_europe',
    'RGI2000-v7.0-G-12_caucasus_middle_east',
    'RGI2000-v7.0-G-13_central_asia',
    'RGI2000-v7.0-G-14_south_asia_west',
    'RGI2000-v7.0-G-15_south_asia_east',
    'RGI2000-v7.0-G-16_low_latitudes',
    'RGI2000-v7.0-G-17_southern_andes',
    'RGI2000-v7.0-G-18_new_zealand',
    'RGI2000-v7.0-G-19_subantarctic_antarctic_islands'
]


def rgi_loader(rgi_dir, rgi_reg):
    # load the RGI outlines
    if os.path.exists(Path(rgi_dir, rgi_reg + '.shp')):
        return Path(rgi_dir, rgi_reg + '.shp')
    elif os.path.exists(Path(rgi_dir, rgi_reg, rgi_reg + '.shp')):
        return Path(rgi_dir, rgi_reg, rgi_reg + '.shp')
    else:
        raise FileNotFoundError(f"Unable to find {rgi_reg}.shp in {rgi_dir}, or a sub-directory. Please check path and filename.")


def generate_geopackage():
    # iterate through csv for each region, create two additional datasets:
    #   - dataset/lakeflags/{region}_lakeflag.gpkg, with the lakeflag CSV joined to the RGI7 centroid (all glaciers)
    #   - dataset/outlines/{region}_laketerminating.gpkg, with outlines for only category 1-3.
    for region in tqdm(rgi_regions):
        fn_csv = region + '_lakeflag.csv'

        lakeflags = pd.read_csv(Path('dataset', 'csv', fn_csv))

        outlines = gpd.read_file(rgi_loader('rgi', region))

        centroids = outlines.copy()
        centroids['geometry'] = gpd.points_from_xy(centroids.cenlon, centroids.cenlat, crs='epsg:4326')

        merged = lakeflags.merge(centroids[['rgi_id', 'geometry']], on='rgi_id')
        gpd.GeoDataFrame(merged).to_file(Path('dataset', 'lakeflags', fn_csv.replace('.csv', '.gpkg')))

        merged = lakeflags.merge(outlines[['rgi_id', 'geometry']], on='rgi_id')
        gpd.GeoDataFrame(merged.loc[merged['lake_cat'].isin([1, 2, 3])]).to_file(
            Path('dataset', 'outlines', fn_csv.replace('lakeflag.csv', 'laketerminating.gpkg'))
        )
