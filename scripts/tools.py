import os
from pathlib import Path


def rgi_loader(rgi_dir, rgi_reg):
    # load the RGI outlines
    if os.path.exists(Path(rgi_dir, rgi_reg + '.shp')):
        return Path(rgi_dir, rgi_reg + '.shp')
    elif os.path.exists(Path(rgi_dir, rgi_reg, rgi_reg + '.shp')):
        return Path(rgi_dir, rgi_reg, rgi_reg + '.shp')
    else:
        raise FileNotFoundError(f"Unable to find {rgi_reg}.shp in {rgi_dir}, or a sub-directory. Please check path and filename.")
