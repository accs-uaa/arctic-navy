# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Prepare fire year data
# Author: Timm Nawrocki
# Last Updated: 2026-01-08
# Usage: Execute in Python 3.9+.
# Description: "Prepare fire year data" extracts fire year raster to common extent, mask, grid, and cell size.
# ---------------------------------------------------------------------------

# Import packages
import os
import time
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling
from akutils import *

# Set nodata value
nodata_value = -32768

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
input_folder = os.path.join(project_folder, 'Data_Input/ancillary_data/Landfire_2023_EVT_30m/unprocessed')
output_folder = os.path.join(project_folder, 'Data_Input/ancillary_data/Landfire_2023_EVT_30m/processed')

# Define input files
area_input = os.path.join(project_folder, 'Data_Input/ArcticCoastal_MapDomain_10m_3338.tif')
landfire_input = os.path.join(input_folder, 'LA23_EVT_240.tif')

# Define output file
landfire_output = os.path.join(output_folder, 'ArcticCoastal_Landfire_10m_3338.tif')

#### PROCESS RASTER EXTRACTION
####____________________________________________________

# Read input rasters
area_raster = rasterio.open(area_input)
landfire_raster = rasterio.open(landfire_input)

# Prepare output profile
output_profile = landfire_raster.profile.copy()
output_profile.update({
    'height': area_raster.height,
    'width': area_raster.width,
    'transform': area_raster.transform,
    'crs': area_raster.crs,
    'nodata': nodata_value,
    'dtype': 'int16',
    'compress': 'lzw',
    'bigtiff': 'YES'
})

# Reproject and extract raster to area
print(f'Reprojecting and extracting input raster to area...')
print(f'Source CRS: {landfire_raster.crs}')
print(f'Target CRS: {area_raster.crs}')
iteration_start = time.time()
with rasterio.open(landfire_output, 'w', **output_profile) as dst:
    # Find number of raster blocks
    window_list = []
    for block_index, window in dst.block_windows(1):
        window_list.append(window)

    # Iterate processing through raster blocks
    count = 1
    progress = 0
    for block_index, window in dst.block_windows(1):
        # Read area block
        area_block = area_raster.read(1, window=window)

        # Create array to store the input raster
        out_block = np.zeros(area_block.shape, dtype=output_profile['dtype'])

        # Calculate the transform for the area raster window
        dst_window_transform = rasterio.windows.transform(window, area_raster.transform)

        # Reproject input raster using warp
        reproject(
            source=rasterio.band(landfire_raster, 1),
            destination=out_block,
            src_transform=landfire_raster.transform,
            src_crs=landfire_raster.crs,
            dst_transform=dst_window_transform,
            dst_crs=area_raster.crs,
            resampling=Resampling.nearest,
            src_nodata=landfire_raster.nodata,
            dst_nodata=nodata_value
        )

        # Set no data values from area raster to no data
        out_block = np.where(area_block == 1, out_block, nodata_value)

        # Write results
        dst.write(out_block,
                  window=window,
                  indexes=1)
        # Report progress
        count, progress = raster_block_progress(100, len(window_list), count, progress)
end_timing(iteration_start)

#### BUILD RASTER PYRAMIDS (OVERVIEWS)
####____________________________________________________

# Define overview levels
overview_levels = [2, 4, 8, 16, 32, 64, 128, 256]

# Build pyramids
print(f'Building pyramids...')
iteration_start = time.time()
with rasterio.open(landfire_output, 'r+') as dst:
    # Build pyramids with bilinear resampling
    dst.build_overviews(overview_levels, resampling=Resampling.mode)
    # Update metadata to indicate overviews exist
    dst.update_tags(ns='rio_overview', resampling='mode')
end_timing(iteration_start)
