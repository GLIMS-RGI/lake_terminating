# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 15:31:31 2024

Script to assign lake-terminating flags to RGI

16 january 2024, william armstrong (armstrongwh@appstate.edu)


@author: armstrongwh
"""


'''
import modules
'''

import fiona
import geopandas as gpd
import pandas as pd

'''
specify filenes
'''
# user will modify filepaths here to point to their own RGI & lake shapefiles

workingPath = '/Users/armstrongwh/Library/CloudStorage/GoogleDrive-armstrongwh@appstate.edu/My Drive/appstate/projects/rgi/'

# RGI shapefiles
rgi01Gfn = workingPath + '/data/rgi70/rgi70_g_test_subset.shp'

# lake shapefiles
rickLakeFn = workingPath + '/data/rick2022/AllLakes_AK_endYear2011.shp'


'''
processing
'''


'''
open rgi, make lists of terminus location lat/lon's

NOTE: This section could easily be streamlined (and probably increased efficiency) using a geopandas geodataframe that pulls termlon and termlat as point geometry. I haven't had time to implement this yet.

'''
rgi01shp = fiona.open(rgi01Gfn)

xList = []
yList = []
rgiList = []

for i in range(0,len(rgi01shp)):
    featNow = rgi01shp[i]
    propsNow = featNow['properties']
    rgiNow = propsNow['rgi_id']
    termX = propsNow['termlon']
    termY = propsNow['termlat']
    
    xList.append(termX)
    yList.append(termY)
    rgiList.append(rgiNow)
    
    utmZone = propsNow['utm_zone']
    


'''
turn terminus locations into geopandas geodatabase

IMPORTANT NOTE - in current implementation, user will need to manually specify UTM for their area of interest. This is done in termGdf_utm variable assignment. You can look up UTM zones at the link below. The EPSG will be 326XX, where XX is the UTM zone number.

UTM zone lookup: https://mangomap.com/robertyoung/maps/69585/what-utm-zone-am-i-in-#
'''

termDf = pd.DataFrame({"long":xList,"lat":yList,'rgi_id':rgiList})    
termGdf = gpd.GeoDataFrame(termDf,crs='epsg:4326',geometry=gpd.points_from_xy(termDf.long,termDf.lat)) # epsg:4326 = wgs84
termGdf_utm = termGdf.to_crs(epsg=32606) # convert to UTM coordinates for buffering (TODO:subset rgi so just have glaciers within same UTM zone? Accomplished this by zooming in, but won't work for entire region)
termGdf_utm_buff1km = gpd.GeoDataFrame.copy(termGdf_utm) # make a copy for working in
termGs_utm_buff1km = termGdf_utm.buffer(1000) # buffer terminus locations by 1 km
termGs_utm_buff1km.to_file(workingPath + 'rgi01_testSubset_term1kmbuff.shp') # save out for plotting
termGdf_utm_buff1km['geometry'] = termGs_utm_buff1km # add buffered terminus positions geoseries to geodatabase as geometry
termGdf_wgs84_buff1km = termGdf_utm_buff1km.to_crs(epsg=4326)  # convert back go wgs84 for spatial join with lake dataset (need matching CRS)


'''
perform spatial joins to find terminus locations overlapping with lake perimeters
'''
rgi01gdf = gpd.read_file(rgi01Gfn) # load in RGI
briLakeGdf = gpd.read_file(rickLakeFn) # load in lake dataset

'''
spatial join without buffer
'''
rgi01gdf_noBuff = gpd.GeoDataFrame.copy(rgi01gdf) # copy rgi for working

joinNoBuff = gpd.sjoin(left_df=termGdf,right_df=briLakeGdf,how='inner') # outputs an index where lakes & rgi extents overlap

lakeTermRgiIdsNoBuff = joinNoBuff['rgi_id'] # pull RGI IDs where lake & glacier termius overlap
lakeTermIndNoBuff = rgi01gdf_noBuff['rgi_id'].isin(lakeTermRgiIdsNoBuff) # index for where those RGI IDs occur in whole RGI dataset
rgi01gdf_noBuff.loc[lakeTermIndNoBuff,'term_type'] = 2 # set term_type for those RGI IDs to 2 (lake-terminating)

# write out
outShapefile = workingPath + 'rgi01_testSubset_withLakeFlag_noBuffer.shp'
rgi01gdf_noBuff.to_file(outShapefile)

'''
spatial join with 1 km terminus buffer
'''

# same steps as above, but join uses the terminus positions buffered by 1 km
rgi01gdf_1kmbuff = gpd.GeoDataFrame.copy(rgi01gdf)

join = gpd.sjoin(left_df=termGdf_wgs84_buff1km,right_df=briLakeGdf,how='inner')

lakeTermRgiIds = join['rgi_id']
lakeTermInd = rgi01gdf_1kmbuff['rgi_id'].isin(lakeTermRgiIds)
rgi01gdf_1kmbuff.loc[lakeTermInd,'term_type'] = 2


outShapefile = workingPath + 'rgi01_testSubset_withLakeFlag_1kmBufffer.shp'
rgi01gdf_1kmbuff.to_file(outShapefile)





