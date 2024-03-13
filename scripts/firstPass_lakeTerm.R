################################################################################
# First pass filter RGI7 vs lake inventory
#
# firstPass_lakeTerm.R
#
# ReadMe: 
# This code does something similar as the python example (see https://github.com/GLIMS-RGI/lake_terminating/tree/main/scripts). It uses the RGI outlines, 
# draws a buffer around the terminus (r=1000 m) or if that is not available in RGI (as for HMA for example) the centroid (r=15 000 m)
# 
#
# Input:  
#         name of contributor
#         choose if buffer is drawn from terminus or centroid
#         template file to be filled with flags (for RGI region, .csv)
#         RGI region inventory (.shp)
#         lake inventory for the same region or a subset of the region (.shp)
#
# Output: 
#         csv file with flags for all glaciers with no lake in vicinity and those with potentially a terminus lake
#         shp file of all RGI7 glaciers that could have a terminus lake for further manual checking 
#
# Created:          2024/02/15
# Latest Revision:  2024/03/13
#
# Jakob Steiner | jakob.steiner@uni-graz.at | fidelsteiner.github.io 
################################################################################
# clear entire workspace (excl. packages)
rm(list = ls())
gc()

# define &-sign for pasting string-elements
'&' <- function(...) UseMethod('&')
'&.default' <- .Primitive('&')
'&.character' <- function(...) paste(...,sep='')

# packages (if not installed yet: install.packages('examplePackage')
library(rgdal)
library(rgeos)
library(maptools)
library(raster)
library(sf)

##################
# input + paths 
##################

flagContrib <- 'Steiner' # surname/identifier of contributor
termDefinition <- 'terminus'    # specify if you want to use the location of the terminus in RGI ('terminus') or the centroid ('centroid') of the glacier to build a search radius 

path_rgi <- 'C:\\Work\\GeospatialData\\RGI70\\RGI2000-v7.0-G-11_central_europe\\' # path for RGI inventory
file_rgi <- 'RGI2000-v7.0-G-11_central_europe.shp'                                # RGI file name

path_lakes <- 'C:\\Work\\Research\\RGI7\\LakeTermini\\LakeInventories\\Alps\\Switzerland\\SwissAlps_lakes_2006_2016\\'  # path for lake inventory
file_lakes <- 'lakes_2006_dsv.shp'                                    # lake file name
DOI_lakes <- 'https://doi.org/10.1594/PANGAEA.934190'                 # DOI of lake inventory

# file name for subset RGI with all glaciers that possibly have a lake
RGI_manipulated <- 'C:\\Work\\Research\\RGI7\\LakeTermini\\RGI11_subset_Switzerland.shp'

# template to fill with all glacier and terminus data (follow original template format in csv!)
outputfile <- 'C:\\Work\\Research\\RGI7\\LakeTermini\\lake_term_data_RGI11.csv' # csv file to be filled with initial flags

##################
# read and intersect lakes with termini
##################

# shp file of the RGI region
RGIfile <- ogrInfo(paste(path_rgi,file_rgi,sep = ""))
RGIfile <- readOGR(dsn=paste(path_rgi,file_rgi,sep = ""))

# shp file of the lake database (to be transformed into crs of RGI)
lakefile <- ogrInfo(paste(path_lakes,file_lakes,sep = ""))
lakefile <- readOGR(dsn=paste(path_lakes,file_lakes,sep = ""))
lakefile <- spTransform(lakefile,crs(RGIfile))

# crop RGI to AOI with lakes                                    ! change manually if lake inventory much smaller/larger than RGI extent
RGI_cropped <- raster::crop(RGIfile,extent(lakefile))
#lakefile <- raster::crop(lakefile,extent(RGIfile))
#RGI_cropped <- RGIfile

vecLakeTerm <- vector(length = length(RGI_cropped))

if(termDefinition=='terminus'){
  bufferR <- 1000
  terminusCoord <- cbind(RGI_cropped$termlon,RGI_cropped$termlat)}
if(termDefinition=='centroid'){
  bufferR <- 15000
  terminusCoord <- cbind(RGI_cropped$cenlon,RGI_cropped$cenlat)}

for(i in 1:length(RGI_cropped)){
terminusCoord_utm  <- st_transform(st_sfc(st_point(terminusCoord[i,]), crs = 4326), "+proj=utm +zone=32")    # change UTM zone here if necessary
circle <- st_buffer(terminusCoord_utm, bufferR) # radius around terminus or centroid (in m)
circle <- st_transform(circle, crs = crs(lakefile))
circle_SPDF <- as(circle, 'Spatial')

{
  res <- try(subsetLakes <- st_as_sf(crop(lakefile,extent(circle_SPDF)+(c(-0.001,0.001,-0.001,0.001)))))
  if(inherits(res, "try-error"))
  {
    next
  }
  if(length(which(unlist(st_intersects(circle, subsetLakes, sparse = F))=='TRUE'))>0){
    vecLakeTerm[i] <- 4 # fill all termini that have a lake in perimeter with 4 as a temporary flag
  }else{
    vecLakeTerm[i] <- 0 # all termini with no lake in vicinity whatsoever are set to flag 0
  }
  if(i %% 100==0) {
    # Print on the screen some message
    cat(paste0("progress: ", i/length(RGI_cropped)*100, "\n%"))
  }
}

}

vecLakeTerm[is.na(vecLakeTerm)] <- 0

# make subset SPDF to use as guideline for final mapping
RGI_subset <- RGI_cropped[which(vecLakeTerm==4),]
writeOGR(obj=RGI_subset, dsn=RGI_manipulated, layer = 'RGI_subset',driver="ESRI Shapefile") 

# fill the template file for eventual export
templateFile <- read.csv(outputfile)
matchSubset <- match(RGIfile$rgi_id,RGI_cropped$rgi_id)

templateFile$rgi_id <- RGIfile$rgi_id
templateFile$lake_terminating_level[which(!is.na(matchSubset))] <- vecLakeTerm
templateFile$inventory_doi[which(!is.na(matchSubset))] <- DOI_lakes
templateFile$contributor[which(!is.na(matchSubset))] <- flagContrib

# Export file to same as input file
write.csv(templateFile, outputfile, row.names=FALSE)
