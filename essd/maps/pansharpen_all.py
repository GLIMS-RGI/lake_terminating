import os
import shutil
import tarfile
from pathlib import Path
from glob import glob
import numpy as np
from osgeo_utils.gdal_pansharpen import gdal_pansharpen
import json
import geoutils as gu


def convert_landsat_bands(granule):

    with open(Path(granule, granule + '_MTL.json'), 'r') as f:
        metadata = json.load(f)
    
    for bn in [2, 3, 4, 8]:
        band = gu.Raster(Path(granule, granule + f"_B{bn}.TIF"))
        band *= float(metadata['LANDSAT_METADATA_FILE']['LEVEL1_RADIOMETRIC_RESCALING'][f"REFLECTANCE_MULT_BAND_{bn}"])
        band += float(metadata['LANDSAT_METADATA_FILE']['LEVEL1_RADIOMETRIC_RESCALING'][f"REFLECTANCE_ADD_BAND_{bn}"])
    
        band.save(Path(granule, f"B{bn}.tif"))


tarballs = glob('*.tar')

for tarball in tarballs:
    print(tarball)
    
    gran = os.path.splitext(tarball)[0]
    os.makedirs(gran, exist_ok=True)

    with tarfile.open(tarball, 'r') as tfile:
        tfile.extractall(gran)
    
    convert_landsat_bands(gran)

    gdal_pansharpen(
        pan_name=os.path.join(gran, 'B8.tif'),
        spectral_names=[os.path.join(gran, f"B{bn}.tif") for bn in [4, 3, 2]],
        dst_filename=f"{gran}_pan.tif"
    )

