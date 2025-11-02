from pathlib import Path
from glob import glob
from delayed_assert import expect, assert_expectations
from git import Repo
import pandas as pd
import geopandas as gpd


def test_column_names():
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
    regions = [fn.split('_lakeflag.csv')[0] for fn in sorted(glob('*lakeflag.csv', root_dir='dataset/csv'))]

    for reg in regions:
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
