from pathlib import Path
from glob import glob
import argparse
from git import Repo
import geopandas as gpd
import pandas as pd
import tools


def _argparser():
    helpstr = """
    Update the "final" dataset files with the changes found in any new or updated contributor files.

    Files in dataset/contributor_files that are tracked by the git repo are compared against the same files on 
    origin/main, as are any untracked CSV files found in dataset/contributor_files. If any changes/updates are found, 
    they will be merged into the corresponding region CSV file (dataset/csv/{region}_lakeflag.csv) as follows:   

    - Any duplicated glaciers where multiple reviewers agree on the lake connectivity category will be included 
      in the output file with their IDs separated by commas (e.g., 01,17,...).
    - Any duplicated glaciers where multiple reviewers do not agree on the lake connectivity category will be
      saved to dataset/contributor_files/{region}/{region}_conflicts.csv for review.
    - Any "missing" glaciers (glaciers included in the RGI region, but not in any contributor file) will be 
      written to a geopackage (.gpkg) file, {region}_missing.gpkg, for review.

    If there are conflicts after running, you can resolve these by editing {region}_conflicts.csv so that the lake
    category for each glacier is the same across different rows. Once all conflicts have been resolved, re-run the
    script and the updates in {region}_conflicts.csv will be merged.

    The following files will be created or updated:
        - dataset/csv/{region}_lakeflag.csv - a CSV table with all non-conflicting lake categories
        - dataset/contributor_files/{region}_conflicts.csv - a CSV table with any conflicting lake categories from
          different contributors, if they are found.
        - {region}_missing.gpkg - a geopackage file with glacier outlines not found in any contributor file. 
        
        If all conflicts have been successfully merged:
        - dataset/lakeflags/{region}_lakeflag.gpkg - a geopackage file of all RGI centroids for {region}, with
          the attributes taken from dataset/csv/{region}_lakeflag.csv
        - dataset/outlines/{region}_laketerminating.gpkg - a geopackage file of RGI outlines for all glaciers with
          a lake-terminating category of 1, 2, or 3.
        - dataset/summary_table.csv - a summary table of the number and area of lake-terminating glaciers in
          each category for each region.
    """
    return argparse.ArgumentParser(description=helpstr, formatter_class=argparse.RawDescriptionHelpFormatter)


def _check_contrib_updates(region, repo):

    contrib_files = [
        f"dataset/contributor_files/{region}/{fn}" for fn in
        glob('**/*.csv', root_dir=f"dataset/contributor_files/{region}", recursive=True)
    ]

    diff = [item.a_path for item in repo.index.diff('origin/main')]

    return list(set(contrib_files) & set(diff)) + list(set(contrib_files) & set(repo.untracked_files))


def _check_csv_updates(repo):
    csv_files = [f"dataset/csv/{reg}_lakeflag.csv" for reg in tools.rgi_regions]
    diff = [item.a_path for item in repo.index.diff('origin/main')]

    file_list = list(set(csv_files) & set(diff))
    if len(file_list) > 0:
        return [fn.split('/')[-1].split('_lakeflag.csv')[0] for fn in file_list]
    else:
        return []


def _merge_contributions(region, updates):
    outlines = gpd.read_file(tools.rgi_loader('rgi', region))

    region_file = pd.read_csv(Path('dataset', 'csv', f"{region}_lakeflag.csv"))

    # check for the existence of a conflict file. if it exists, use this instead of the updated files.
    conflict_file = Path('dataset', 'contributor_files', region, f"{region}_conflicts.csv")
    if conflict_file.exists():
        combined = pd.concat([region_file, pd.read_csv(conflict_file)],
                             ignore_index=True).sort_values('rgi_id').reset_index(drop=True)
    else:
        combined = pd.concat([region_file] + [pd.read_csv(fn) for fn in updates],
                             ignore_index=True).sort_values('rgi_id').reset_index(drop=True)

    combined['contributor'] = combined['contributor'].astype(str)

    missing = outlines[~outlines['rgi_id'].isin(combined['rgi_id'])]
    if len(missing) > 0:
        print(f"Found {len(missing)} glaciers not included in contributions. Saving to {region}_missing.gpkg")
        missing.to_file(f"{region}_missing.gpkg")
    else:
        print(f"{region}: No missing glaciers found.")

    # find any ids that are duplicated in the table
    dup_ids = combined.loc[combined.duplicated(subset='rgi_id'), 'rgi_id']

    # get all glaciers with no duplication
    output = combined.loc[~combined['rgi_id'].isin(dup_ids)]

    # get all duplicated rgi ids
    duplicated = combined.loc[combined['rgi_id'].isin(dup_ids)]

    # split duplicates into conflicts, agreement based on lake category
    conflicts = duplicated.loc[~duplicated.duplicated(['rgi_id', 'lake_cat'], keep=False)].sort_values('rgi_id')
    agreed = duplicated.loc[duplicated.duplicated(['rgi_id', 'lake_cat'], keep=False)].sort_values('rgi_id')

    # if there are conflicts (different lake category), save these to a file for review
    if len(conflicts) > 0:
        nconflicts = len(conflicts['rgi_id'].unique())
        print(f"{region}: Found {nconflicts} disagreements on lake category. Saving to {conflict_file}")
        conflicts.to_csv(conflict_file, index=False)

    # if there are no conflicts, combine the contributor names
    if len(agreed) > 0:
        nagreed = len(agreed['rgi_id'].unique())
        print(f"{region}: Found {nagreed} duplicated agreed glaciers. Combining contributor names.")
        contribs = agreed.sort_values(['rgi_id', 'contributor']).groupby('rgi_id')['contributor'].apply(
            ', '.join).reset_index()

        clean_agreed = agreed.drop_duplicates('rgi_id').drop(columns=['contributor'])
        output = pd.concat([output,
                            clean_agreed.merge(contribs, left_on='rgi_id', right_on='rgi_id')], ignore_index=True)

    # save the final combined file without the conflicts
    print(f"{region}: Writing combined output to dataset/csv/{region}_lakeflag.csv")
    output.sort_values('rgi_id').to_csv(Path('dataset', 'csv', f"{region}_lakeflag.csv"), index=False)

    return len(conflicts)


def main():
    repo = Repo('.')

    nconflicts = 0
    for region in tools.rgi_regions:
        # first, check for any contributor updates; if they exist, try to merge them
        updates = _check_contrib_updates(region, repo)
        if len(updates) == 0:
            pass
        else:
            print(f"Found new/updated contributions in {region}. Attempting to merge updates.")
            nconflicts += _merge_contributions(region, updates)

    assert nconflicts == 0, "Found unresolved conflicts. Please ensure that any *conflicts.csv files have been " + \
        "modified to resolve conflicting lake category values, then re-run the script."

    # next, check if the actual csv files have been updated.
    needs_updated = _check_csv_updates(repo)

    if len(needs_updated) > 0:
        print("CSV files have been updated. Re-creating geopackage files.")
        tools.generate_geopackage(needs_updated)

        print("Updating dataset/summary_table.csv.")
        tools.summary_table()
    else:
        pass

    print("Finished updating.")


if __name__ == "__main__":
    parser = _argparser()
    args = parser.parse_args()

    main()
