import argparse
import geopandas as gpd
import tools


def _argparser():
    helpstr = """
    Use an existing lake inventory to assign the 'term_type' flag for RGI outlines by spatially joining the lake 
    outlines with buffered and unbuffered terminus locations.
    """
    parser = argparse.ArgumentParser(description=helpstr,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('rgi_directory', action='store', type=str,
                        help='The path to the directory containing the RGI region sub-directories.')
    parser.add_argument('rgi_region', action='store', type=str,
                        help='The name of the RGI v7 region to use (e.g., "RGI2000-v7.0-G-01_alaska").')
    parser.add_argument('lake_outlines', action='store', type=str,
                        help='The filename for the lake inventory to use.')
    parser.add_argument('-epsg', action='store', type=int,
                        help='The EPSG code for the projected CRS to use for buffering the RGI terminus lat/lon. If '
                             'not set, will use gpd.GeoDataFrame.estimate_utm_crs() to project the terminus points.')
    parser.add_argument('-b', '--buffer', action='store', type=int, default=1000,
                        help='The buffer size (in m) to use for buffering the terminus points. Defaults to 1000 m.')

    return parser


def main():
    parser = _argparser()
    args = parser.parse_args()

    fn_outlines = tools.rgi_loader(args.rgi_directory, args.rgi_region)

    outlines = gpd.read_file(fn_outlines)

    # get a geodataframe of the terminus positions
    terms = outlines.copy()
    terms['geometry'] = gpd.points_from_xy(terms['termlon'], terms['termlat'], crs='epsg:4326')

    # if we aren't given an EPSG, default to using gdf.estimate_utm_crs()
    if args.epsg is None:
        proj_crs = outlines.estimate_utm_crs()
    else:
        proj_crs = f"epsg:{args.epsg}"

    # project, then buffer the terminus positions
    terms_buff = terms.to_crs(proj_crs)
    terms_buff['geometry'] = terms.to_crs(proj_crs).buffer(args.buffer)

    # load the lake outlines
    lake_outlines = gpd.read_file(args.lake_outlines)

    # join the lakes to the un-buffered terminus positions
    join_nobuff = gpd.sjoin(left_df=terms.to_crs(lake_outlines.crs),
                            right_df=lake_outlines,
                            how='inner')

    outlines_nobuff = outlines[['geometry', 'rgi_id', 'term_type']].copy()
    outlines_nobuff['lake_level'] = ''
    outlines_nobuff['img_id'] = ''
    outlines_nobuff['img_date'] = ''
    outlines_nobuff['inv_doi'] = ''
    outlines_nobuff['cont'] = ''
    outlines_nobuff['notes'] = ''

    # only want to change term_type if it hasn't been set (i.e., equal to 9)
    outlines_nobuff.loc[(outlines.index.isin(join_nobuff.index)) & (outlines.term_type == 9), 'term_type'] = 2
    outlines_nobuff.to_file(f"{args.rgi_region}_lakeflag_nobuffer.shp")

    # join the lakes to the buffered terminus positions
    join_buff = gpd.sjoin(left_df=terms_buff.to_crs(lake_outlines.crs),
                          right_df=lake_outlines,
                          how='inner')

    outlines_buff = outlines[['geometry', 'rgi_id', 'term_type']].copy()
    outlines_buff['lake_level'] = ''
    outlines_buff['img_id'] = ''
    outlines_buff['img_date'] = ''
    outlines_buff['inv_doi'] = ''
    outlines_buff['cont'] = ''
    outlines_buff['notes'] = ''

    # only want to change term_type if it hasn't been set (i.e., equal to 9)
    outlines_buff.loc[(outlines.index.isin(join_buff.index)) & (outlines.term_type == 9), 'term_type'] = 2
    outlines_buff.to_file(f"{args.rgi_region}_lakeflag_{args.buffer}m_buffer.shp")


if __name__ == "__main__":
    main()

