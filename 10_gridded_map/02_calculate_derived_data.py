# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Calculate derived data
# Author: Timm Nawrocki
# Last Updated: 2025-04-08
# Usage: Execute in Python 3.9+.
# Description: "Calculate derived data" calculates new metrics from the foliar cover maps.
# ---------------------------------------------------------------------------

# Import packages
import os
import time
import numpy as np
import rasterio
from akutils import *

# Set no data value
nodata = 255

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
foliar_folder = os.path.join(project_folder, 'Data_Input/foliar_data')
derived_folder = os.path.join(project_folder, 'Data_Input/derived_data')

# Define input files
area_input = os.path.join(project_folder, 'Data_Input/ArcticCoastal_MapDomain_10m_3338.tif')
alnus_input = os.path.join(foliar_folder, 'alnus_10m_3338.tif')
betshr_input = os.path.join(foliar_folder, 'betshr_10m_3338.tif')
erivag_input = os.path.join(foliar_folder, 'erivag_10m_3338.tif')
nerishr_input = os.path.join(foliar_folder, 'nerishr_10m_3338.tif')
rhoshr_input = os.path.join(foliar_folder, 'rhoshr_10m_3338.tif')
salshr_input = os.path.join(foliar_folder, 'ndsalix_10m_3338.tif')
sphagn_input = os.path.join(foliar_folder, 'sphagn_10m_3338.tif')
vacvit_input = os.path.join(foliar_folder, 'vacvit_10m_3338.tif')
wetsed_input = os.path.join(foliar_folder, 'wetsed_10m_3338.tif')
lichen_input = os.path.join(foliar_folder, 'lichen_10m_3338.tif')
gramin_input = os.path.join(foliar_folder, 'gramin_10m_3338.tif')
forb_input = os.path.join(foliar_folder, 'forb_10m_3338.tif')

# Define output files
ndshrub_output = os.path.join(derived_folder, 'alder_birch_willow_10m_3338.tif')
eridwarf_output = os.path.join(derived_folder, 'ericaceous_dwarf_10m_3338.tif')
wetland_output = os.path.join(derived_folder, 'wetland_indicator_10m_3338.tif')
herbaceous_output = os.path.join(derived_folder, 'herbaceous_10m_3338.tif')

# Open area raster
area_raster = rasterio.open(area_input)

# Calculate non-dwarf shrub output
if os.path.exists(ndshrub_output) == 0:
    print(f'Calculating non-dwarf shrub sum...')
    iteration_start = time.time()
    alnus_raster = rasterio.open(alnus_input)
    betshr_raster = rasterio.open(betshr_input)
    salshr_raster = rasterio.open(salshr_input)
    input_profile = alnus_raster.profile.copy()
    with rasterio.open(ndshrub_output, 'w', **input_profile, BIGTIFF='YES') as dst:
        # Find number of raster blocks
        window_list = []
        for block_index, window in area_raster.block_windows(1):
            window_list.append(window)
        # Iterate processing through raster blocks
        count = 1
        progress = 0
        for block_index, window in area_raster.block_windows(1):
            area_block = area_raster.read(window=window, masked=False)
            alnus_block = alnus_raster.read(window=window, masked=False)
            salshr_block = salshr_raster.read(window=window, masked=False)
            betshr_block = betshr_raster.read(window=window, masked=False)
            # Calculate ndshrub sum
            raster_block = alnus_block + salshr_block + betshr_block
            # Set no data values from area raster to no data
            raster_block = np.where(area_block != 1, nodata, raster_block)
            # Write results
            dst.write(raster_block, window=window)
            # Report progress
            count, progress = raster_block_progress(10, len(window_list), count, progress)
    end_timing(iteration_start)

# Calculate ericaceous dwarf shrub output
if os.path.exists(eridwarf_output) == 0:
    print(f'Calculating ericaceous dwarf shrub sum...')
    iteration_start = time.time()
    nerishr_raster = rasterio.open(nerishr_input)
    rhoshr_raster = rasterio.open(rhoshr_input)
    vacvit_raster = rasterio.open(vacvit_input)
    input_profile = nerishr_raster.profile.copy()
    with rasterio.open(eridwarf_output, 'w', **input_profile, BIGTIFF='YES') as dst:
        # Find number of raster blocks
        window_list = []
        for block_index, window in area_raster.block_windows(1):
            window_list.append(window)
        # Iterate processing through raster blocks
        count = 1
        progress = 0
        for block_index, window in area_raster.block_windows(1):
            area_block = area_raster.read(window=window, masked=False)
            nerishr_block = nerishr_raster.read(window=window, masked=False)
            rhoshr_block = rhoshr_raster.read(window=window, masked=False)
            vacvit_block = vacvit_raster.read(window=window, masked=False)
            # Calculate ericaceous dwarf shrub sum
            raster_block = nerishr_block + rhoshr_block + vacvit_block
            # Set no data values from area raster to no data
            raster_block = np.where(area_block != 1, nodata, raster_block)
            # Write results
            dst.write(raster_block, window=window)
            # Report progress
            count, progress = raster_block_progress(10, len(window_list), count, progress)
    end_timing(iteration_start)

# Calculate wetland indicator
if os.path.exists(wetland_output) == 0:
    print(f'Calculating wetland indicator...')
    iteration_start = time.time()
    wetsed_raster = rasterio.open(wetsed_input)
    sphagn_raster = rasterio.open(sphagn_input)
    input_profile = wetsed_raster.profile.copy()
    with rasterio.open(wetland_output, 'w', **input_profile, BIGTIFF='YES') as dst:
        # Find number of raster blocks
        window_list = []
        for block_index, window in area_raster.block_windows(1):
            window_list.append(window)
        # Iterate processing through raster blocks
        count = 1
        progress = 0
        for block_index, window in area_raster.block_windows(1):
            area_block = area_raster.read(window=window, masked=False)
            sphagn_block = sphagn_raster.read(window=window, masked=False)
            wetsed_block = wetsed_raster.read(window=window, masked=False)
            # Calculate wetland indicator
            raster_block = sphagn_block + wetsed_block
            # Set no data values from area raster to no data
            raster_block = np.where(area_block != 1, nodata, raster_block)
            # Write results
            dst.write(raster_block, window=window)
            # Report progress
            count, progress = raster_block_progress(10, len(window_list), count, progress)
    end_timing(iteration_start)

# Calculate herbaceous output
if os.path.exists(herbaceous_output) == 0:
    print(f'Calculating herbaceous output...')
    iteration_start = time.time()
    forb_raster = rasterio.open(forb_input)
    gramin_raster = rasterio.open(gramin_input)
    erivag_raster = rasterio.open(erivag_input)
    wetsed_raster = rasterio.open(wetsed_input)
    input_profile = wetsed_raster.profile.copy()
    with rasterio.open(herbaceous_output, 'w', **input_profile, BIGTIFF='YES') as dst:
        # Find number of raster blocks
        window_list = []
        for block_index, window in area_raster.block_windows(1):
            window_list.append(window)
        # Iterate processing through raster blocks
        count = 1
        progress = 0
        for block_index, window in area_raster.block_windows(1):
            area_block = area_raster.read(window=window, masked=False)
            forb_block = forb_raster.read(window=window, masked=False)
            gramin_block = gramin_raster.read(window=window, masked=False)
            erivag_block = erivag_raster.read(window=window, masked=False)
            wetsed_block = wetsed_raster.read(window=window, masked=False)
            # Calculate herbaceous cover
            raster_block = (forb_block + gramin_block) - (erivag_block + wetsed_block)
            # Set no data values from area raster to no data
            raster_block = np.where(raster_block < 0, 0, raster_block)
            raster_block = np.where(area_block != 1, nodata, raster_block)
            # Write results
            dst.write(raster_block, window=window)
            # Report progress
            count, progress = raster_block_progress(10, len(window_list), count, progress)
    end_timing(iteration_start)
