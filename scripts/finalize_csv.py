import os
import argparse
import geopandas as gpd
import pandas as pd


def _argparser():
    helpstr = """
    Convert an RGI Lakes shapefile attribute table into a CSV file.
    """
    parser = argparse.ArgumentParser(description=helpstr,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('fn_outlines', action='store', type=str,
                        help='The filename of the outlines shapefile or CSV to convert.')
    parser.add_argument('contributor', action='store', type=str,
                        help='The surname of the contributor who did the mapping.')
    parser.add_argument('-doi', action='store', type=str, default=None,
                        help='The DOI (or other identifier) for the lake inventory (if used).')
    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()

    fn_out = '_'.join([os.path.splitext(os.path.basename(args.fn_outlines))[0],
                       args.contributor.lower() + '.csv'])  # the name of the csv file to write out

    outlines = gpd.read_file(args.fn_outlines)
    # set image date using the image id - currently assumes that the img_id is a landsat product id
    outlines['img_date'] = pd.to_datetime(outlines['img_id'].str.split('_').str[3]).dt.strftime('%Y-%m-%d')

    outlines['cont'] = args.contributor
    
    if args.doi is not None:
        outlines['inv_doi'] = args.doi

    # drop any null lake_level values, then ensure that this column is an integer
    outlines.dropna(subset=['lake_level'], inplace=True)
    outlines['lake_level'] = outlines['lake_level'].astype(int)

    # change the column names since we're not bound by esri rules with the csv
    outlines.rename(columns={'term_type': 'auto_term', 'inv_doi': 'inventory_doi',
                             'cont': 'contributor', 'img_id': 'image_id',
                             'img_date': 'image_date'}, inplace=True)

    # remove the geometry column before writing to csv
    colnames = list(outlines.columns)
    colnames.remove('geometry')

    outlines[colnames].to_csv(fn_out, index=False)


if __name__ == "__main__":
    main()


