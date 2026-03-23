# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Prepare foliar cover (30 m) data
# Author: Timm Nawrocki
# Last Updated: 2026-01-04
# Usage: Execute in Python 3.9+.
# Description: "Prepare foliar cover (30 m) data" extracts rasters to common extent, mask, grid, and cell size.
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
nodata_value = 255

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
above_folder = os.path.join(drive, root_folder, 'Data/biota/vegetation/Alaska_PFT_TimeSeries/original')
output_folder = os.path.join(project_folder, 'Data_Input/foliar_data')

# Define input files
area_input = os.path.join(project_folder, 'Data_Input/ArcticCoastal_MapDomain_10m_3338.tif')

# Create input list for foliar cover maps
foliar_list = ['tmLichenLight', 'Graminoid', 'Forb']
foliar_names = ['lichen', 'gramin', 'forb']

#### PROCESS RASTER EXTRACTION
####____________________________________________________

# Process foliar cover rasters (30 m)
for name in foliar_list:
    # Define input file
    foliar_input = os.path.join(above_folder, 'ABoVE_PFT_Top_Cover_' + name + '_2020.tif')

    # Define output file
    output_name = foliar_names[foliar_list.index(name)]
    foliar_output = os.path.join(output_folder, output_name + '_10m_3338.tif')

    # Create output file if it does not exist
    if os.path.exists(foliar_output) == 0:
        # Read input rasters
        area_raster = rasterio.open(area_input)
        foliar_raster = rasterio.open(foliar_input)

        # Prepare output profile
        output_profile = foliar_raster.profile.copy()
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
        print(f'Extracting {name} raster to area...')
        iteration_start = time.time()
        with rasterio.open(foliar_output, 'w', **output_profile) as dst:
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
                    source=rasterio.band(foliar_raster, 1),
                    destination=out_block,
                    src_transform=foliar_raster.transform,
                    src_crs=foliar_raster.crs,
                    dst_transform=dst_window_transform,
                    dst_crs=area_raster.crs,
                    resampling=Resampling.bilinear,
                    src_nodata=foliar_raster.nodata,
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
        print('Building pyramids...')
        iteration_start = time.time()
        with rasterio.open(foliar_output, 'r+') as dst:
            # Build pyramids with bilinear resampling
            dst.build_overviews(overview_levels, resampling=Resampling.bilinear)
            # Update metadata to indicate overviews exist
            dst.update_tags(ns='rio_overview', resampling='bilinear')
        end_timing(iteration_start)
