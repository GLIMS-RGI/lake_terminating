import argparse
from glob import glob
import geopandas as gpd
import pandas as pd
import tools


def _argparser():
    helpstr = """
    Combine multiple reviewer contributions for a given RGI region into a single CSV, {region}_lakeflag.csv. 
    
    Any duplicated glaciers where multiple reviewers agree on the lake connectivity level will be included in the output
    file with their names separated by commas (e.g., Armstrong, Bolch, ...). 
    
    Any duplicated glaciers where multiple reviewers do not agree on the lake connectivity level will be saved to 
    {region}_conflicts.csv for review.
    
    Any "missing" glaciers (glaciers included in the RGI region, but not in any contributor file) will be written to a 
    geopackage (.gpkg) file, {region}_missing.gpkg, for review.
    
    If there are conflicts after running, you can resolve these by editing {region}_conflicts.csv. Once this is done,
    re-run this script using the -m (or --merge) flag to merge the resolved conflicts.
    
    When there are no conflicts, and no missing glaciers, the final CSV file ({region}_lakeflag.csv) can be uploaded
    to github.
    
    Outputs
        - {region}_lakeflag.csv - a CSV table with all non-conflicting lake levels
        - {region}_conflicts.csv - a CSV table with any conflicting lake levels from different contributors
        - {region}_missing.gpkg - a geopackage file with glacier outlines not found in any contributor file. 

    """
    parser = argparse.ArgumentParser(description=helpstr,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('rgi_directory', action='store', type=str,
                        help='The path to the directory containing the RGI region files or sub-directories.')
    parser.add_argument('rgi_region', action='store', type=str,
                        help='The name of the RGI v7 region to use (e.g., "RGI2000-v7.0-G-01_alaska").')
    parser.add_argument('-m', '--merge', action='store_true',
                        help='Merge (resolved) conflicts file with existing consensus attributes.')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()

    outlines = gpd.read_file(tools.rgi_loader(args.rgi_directory, args.rgi_region))
    if not args.merge:
        csv_list = sorted(glob(f"{args.rgi_region}_lakeflag_*.csv"))
        combined = pd.concat([pd.read_csv(fn) for fn in csv_list],
                             ignore_index=True).sort_values('rgi_id').reset_index(drop=True)
    else:
        print("Attempting to merge resolved conflicts file.")
        combined = pd.concat([pd.read_csv(f"{args.rgi_region}_lakeflag.csv"),
                              pd.read_csv(f"{args.rgi_region}_conflicts.csv")],
                             ignore_index=True).sort_values('rgi_id').reset_index(drop=True)

    # find any glaciers not included in our contributions
    missing = outlines[~outlines['rgi_id'].isin(combined['rgi_id'])]
    if len(missing) > 0:
        print(f"Found {len(missing)} glaciers not included in contributions. Saving to {args.rgi_region}_missing.gpkg")
        missing.to_file(f"{args.rgi_region}_missing.gpkg")
    else:
        print("No missing glaciers found.")

    # find any ids that are duplicated in the table
    dup_ids = combined.loc[combined.duplicated(subset='rgi_id'), 'rgi_id']

    # get all glaciers with no duplication
    output = combined.loc[~combined['rgi_id'].isin(dup_ids)]

    # get all duplicated rgi ids
    duplicated = combined.loc[combined['rgi_id'].isin(dup_ids)]

    # split duplicates into conflicts, agreement based on lake level
    conflicts = duplicated.loc[~duplicated.duplicated(['rgi_id', 'lake_level'], keep=False)].sort_values('rgi_id')
    agreed = duplicated.loc[duplicated.duplicated(['rgi_id', 'lake_level'], keep=False)].sort_values('rgi_id')

    # if there are conflicts (different lake level), save these to a file for review
    if len(conflicts) > 0:
        nconflicts = len(conflicts['rgi_id'].unique())
        print(f"Found {nconflicts} disagreements on lake level. Saving to {args.rgi_region}_conflicts.csv")
        conflicts.to_csv(f"{args.rgi_region}_conflicts.csv", index=False)

    # if there are no conflicts, combine the contributor names
    if len(agreed) > 0:
        nagreed = len(agreed['rgi_id'].unique())
        print(f"Found {nagreed} duplicated agreed glaciers. Combining contributor names.")
        contribs = agreed.sort_values(['rgi_id', 'contributor']).groupby('rgi_id')['contributor'].apply(
            ', '.join).reset_index()

        clean_agreed = agreed.drop_duplicates('rgi_id').drop(columns=['contributor'])
        output = pd.concat([output,
                            clean_agreed.merge(contribs, left_on='rgi_id', right_on='rgi_id')], ignore_index=True)

    # save the final combined file without the conflicts
    print(f"Writing combined output to {args.rgi_region}_lakeflag.csv")
    output.sort_values('rgi_id').to_csv(f"{args.rgi_region}_lakeflag.csv", index=False)


if __name__ == "__main__":
    main()

