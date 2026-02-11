import os
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import geopandas as gpd
from typing import Union


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


def rgi_loader(rgi_dir: Union[str, Path], rgi_reg: Union[str, Path]) -> Path:
    """
    Returns the path to the RGI 7.0 shapefile for the given region. Checks whether RGI files are stored in a single
    directory, or in sub-directories.

    :param rgi_dir: The path to the directory where the RGI files or folders are stored.
    :param rgi_reg: The RGI 7.0 region name (e.g., RGI2000-v7.0-G-01_alaska)
    """
    # load the RGI outlines
    if os.path.exists(Path(rgi_dir, rgi_reg + '.shp')):
        return Path(rgi_dir, rgi_reg + '.shp')
    elif os.path.exists(Path(rgi_dir, rgi_reg, rgi_reg + '.shp')):
        return Path(rgi_dir, rgi_reg, rgi_reg + '.shp')
    else:
        raise FileNotFoundError(f"Unable to find {rgi_reg}.shp in {rgi_dir}, or a sub-directory. Please check path and filename.")


def generate_geopackage(regions: Union[None, list] = None) -> None:
    """
    For each RGI region, create two additional datasets:

    - dataset/lakeflags/{region}_lakeflag.gpkg, with the lakeflag CSV joined to the RGI7 centroid (all glaciers)
    - dataset/outlines/{region}_laketerminating.gpkg, with outlines for lake category 1-3.

    :param regions: The list of regions to update. If None, updates all files.
    """

    if regions is None:
        regions = rgi_regions

    for region in tqdm(regions):
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


def summary_table() -> None:
    """
    Read all regional CSVs in dataset/csv, and write a table summarizing the number and area of glaciers in
    each category.

    """

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

    for region in rgi_regions:
        fn_csv = region + '_lakeflag.csv'

        num, name = region.split('-')[-1].split('_', maxsplit=1)

        lakeflags = pd.read_csv(Path('dataset', 'csv', fn_csv))
        outlines = gpd.read_file(rgi_loader('rgi', region))

        lakeflags = lakeflags.merge(outlines[['rgi_id', 'area_km2']], left_on='rgi_id', right_on='rgi_id')

        regions.append(int(num))
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

    global_counts.to_csv(Path('dataset', 'regional_summary.csv'))
