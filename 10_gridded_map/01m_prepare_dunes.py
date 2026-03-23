# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Prepare dunes data
# Author: Timm Nawrocki
# Last Updated: 2026-01-08
# Usage: Execute in Python 3.9+.
# Description: "Prepare dunes data" extracts dune raster modified from Arctic Coastal Plain geomorphology to common extent, mask, grid, and cell size.
# ---------------------------------------------------------------------------

# Import packages
import os
import time
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import Resampling
from akutils import *

# Set nodata value
nodata_value = 255

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
input_folder = os.path.join(project_folder,
                            'Data_Input/ancillary_data/ArcticCoastal_Geomorphology_30m/unprocessed')
output_folder = os.path.join(project_folder,
                             'Data_Input/ancillary_data/ArcticCoastal_Geomorphology_30m/processed')

# Define input files
area_input = os.path.join(project_folder, 'Data_Input/ArcticCoastal_MapDomain_10m_3338.tif')
dune_input = os.path.join(input_folder,
                          'NorthernAlaska_CoastalPlain_Geomorphology_Dunes_Buff100_10m_3338.tif')

# Define output file
dune_output = os.path.join(output_folder, 'ArcticCoastal_Dunes_10m_3338.tif')

#### PROCESS RASTER EXTRACTION
####____________________________________________________

# Read input rasters
area_raster = rasterio.open(area_input)
dune_raster = rasterio.open(dune_input)

# Prepare output profile
output_profile = dune_raster.profile.copy()
output_profile.update({
    'height': area_raster.height,
    'width': area_raster.width,
    'transform': area_raster.transform,
    'crs': area_raster.crs,
    'nodata': nodata_value,
    'dtype': 'uint8',
    'compress': 'lzw',
    'bigtiff': 'YES'
})

# Extract raster to area
print(f'Extracting raster to area...')
iteration_start = time.time()
with rasterio.open(dune_output, 'w', **output_profile) as dst:
    # Find number of raster blocks
    window_list = []
    for block_index, window in dst.block_windows(1):
        window_list.append(window)
    # Iterate processing through raster blocks
    count = 1
    progress = 0
    for block_index, window in dst.block_windows(1):
        # Compute bounds of the current output window
        window_bounds = rasterio.windows.bounds(window, area_raster.transform)

        # Compute the corresponding window in input raster
        input_window = from_bounds(*window_bounds,
                                   transform=dune_raster.transform).round_offsets().round_lengths()

        # Read block data
        area_block = area_raster.read(1, window=window)
        out_block = dune_raster.read(1, window=input_window)

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
with rasterio.open(dune_output, 'r+') as dst:
    # Build pyramids with bilinear resampling
    dst.build_overviews(overview_levels, resampling=Resampling.mode)
    # Update metadata to indicate overviews exist
    dst.update_tags(ns='rio_overview', resampling='mode')
end_timing(iteration_start)
