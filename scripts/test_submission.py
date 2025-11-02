from pathlib import Path
from glob import glob
from delayed_assert import expect, assert_expectations
from git import Repo
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

def test_columns():
    """
    Checks that each new/updated file in dataset/csv and dataset/contributor_files has the correct columns, based on
    what is found in lake_term_data_template.csv:

    rgi_id,lake_cat,image_id,image_date,inventory_doi,contributor

    Raises an AssertionError if one or more files is missing one or more columns.

    """
    # check all files in dataset/contributor_files/
    contribs = [f"dataset/csv/{fn}" for fn in glob('**/*.csv',
                                                   root_dir='dataset/csv',
                                                   recursive=True)] \
               + [f"dataset/contributor_files/{fn}" for fn in glob('**/*.csv',
                                                                   root_dir='dataset/contributor_files',
                                                                   recursive=True)]

    # get a list of "new" or changed files from the current branch
    repo = Repo('.')
    diff = [item.a_path for item in repo.index.diff('main')]

    new_contribs = list(set(contribs) & set(diff))

    print(f"Found {len(new_contribs)} new or changed submissions: ")
    for fn in new_contribs:
        print(fn)

    # required columns
    req_cols = pd.read_csv('lake_term_data_template.csv').columns

    for fn_csv in new_contribs:
        csv = pd.read_csv(fn_csv)
        # first, check that columns are all there.
        for col in req_cols:
            expect(col in csv.columns, f"{col} not found in {fn_csv}: \n{list(csv.columns)}")

    assert_expectations()


def test_geopackage():
    """
    Tests whether all geopackage files (a) exist for each region, and (b) have the correct column names.
    """
    req_cols = pd.read_csv('lake_term_data_template.csv').columns

    for reg in rgi_regions:
        expect(Path('dataset', 'lakeflags', f"{reg}_lakeflag.gpkg").exists(),
               f"geopackage file not found in dataset/lakeflags/ for {reg}")
        expect(Path('dataset', 'outlines', f"{reg}_laketerminating.gpkg").exists(),
               f"geopackage file not found in dataset/outlines/ for {reg}")

        lakeflag = gpd.read_file(Path('dataset', 'lakeflags', f"{reg}_lakeflag.gpkg"))
        outlines = gpd.read_file(Path('dataset', 'outlines', f"{reg}_laketerminating.gpkg"))

        for col in req_cols:
            expect(col in lakeflag.columns, f"{col} not found in {reg} lakeflag file: \n{list(lakeflag.columns)}")
            expect(col in outlines.columns, f"{col} not found in {reg} outlines file: \n{list(outlines.columns)}")

    assert_expectations()


def test_lake_cat():
    """
    Tests whether the lake_cat value is the same in the csv tables and the geopackage files for all regions.
    """

    for reg in rgi_regions:
        attributes = pd.read_csv(Path('dataset', 'csv', f"{reg}_lakeflag.csv")).set_index('rgi_id')

        lakeflag = gpd.read_file(Path('dataset', 'lakeflags', f"{reg}_lakeflag.gpkg")).set_index('rgi_id')
        outlines = gpd.read_file(Path('dataset', 'outlines', f"{reg}_laketerminating.gpkg")).set_index('rgi_id')

        # can compare these directly, as they should be identically indexed (and if not, it's an error)
        expect((attributes['lake_cat'] == lakeflag['lake_cat']).all(),
               f"lake_cat doesn't match for {reg} points file.")

        # have to first select from attributes where index is also in outlines
        same_index = attributes.index[attributes.index.isin(outlines.index)]
        expect((attributes.loc[same_index, 'lake_cat'] == outlines['lake_cat']).all(),
               f"lake_cat doesn't match for {reg} outlines.")

    assert_expectations()
