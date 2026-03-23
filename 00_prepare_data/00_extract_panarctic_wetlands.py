# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Extract Panarctic Wetlands
# Author: Timm Nawrocki
# Last Updated: 2026-01-03
# Usage: Must be executed in a Python 3.12+ installation.
# Description: "Extract Panarctic Wetlands" extracts the panarctic wetland dataset to the AKVEG Map Domain and reprojects it to Alaska Albers Equal Area Conic.
# ---------------------------------------------------------------------------

# Import packages
import os
import time
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling
import collections
import dbf
from akutils import *

# Set no data
nodata_value = 255

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
akveg_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/AKVEG_Map/Data')
input_folder = os.path.join(project_folder, 'Data_Input/ancillary_data/Panarctic_Wetlands_10m')

# Define input files
area_input = os.path.join(akveg_folder, 'Data_Input', 'AlaskaYukon_MapDomain_10m_3338.tif')
wetland_input = os.path.join(input_folder, 'unprocessed',
                             'Circumarctic_PanarcticWetland_v1.0_10m_3573.tif')

# Define output file
wetland_output = os.path.join(input_folder, 'processed',
                              'AlaskaYukon_PanarcticWetland_v1.0_10m_3338.tif')

#### PROCESS RASTER EXTRACTION
####____________________________________________________

# Read input rasters
area_raster = rasterio.open(area_input)
wetland_raster = rasterio.open(wetland_input)

# Prepare output profile
output_profile = wetland_raster.profile.copy()
output_profile.update({
    'height': area_raster.height,
    'width': area_raster.width,
    'transform': area_raster.transform,
    'crs': area_raster.crs,
    'nodata': nodata_value,
    'compress': 'lzw',
    'bigtiff': 'YES'
})

# Reproject and extract raster to area
print(f'Reprojecting and extracting input raster to area...')
print(f'Source CRS: {wetland_raster.crs}')
print(f'Target CRS: {area_raster.crs}')
iteration_start = time.time()
with rasterio.open(wetland_output, 'w', **output_profile) as dst:
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
            source=rasterio.band(wetland_raster, 1),
            destination=out_block,
            src_transform=wetland_raster.transform,
            src_crs=wetland_raster.crs,
            dst_transform=dst_window_transform,
            dst_crs=area_raster.crs,
            resampling=Resampling.nearest,
            src_nodata=wetland_raster.nodata,
            dst_nodata=nodata_value
        )

        # Remove zero values
        out_block = np.where(out_block == 0, nodata_value, out_block)

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
with rasterio.open(wetland_output, 'r+') as dst:
    # Build pyramids with modal resampling
    dst.build_overviews(overview_levels, resampling=Resampling.mode)
    # Update metadata to indicate overviews exist
    dst.update_tags(ns='rio_overview', resampling='mode')
end_timing(iteration_start)

#### BUILD RASTER ATTRIBUTE TABLE
####____________________________________________________

# Create dictionary of value labels
value_labels = {
    1: 'Bog',
    2: 'Fen',
    3: 'Swamp',
    4: 'Marsh',
    5: 'Water',
    6: 'Snow/Ice',
    7: 'Upland'
}

# Specify attribute table file path
attribute_output = wetland_output + '.vat.dbf'
if os.path.exists(attribute_output):
    os.remove(attribute_output)

# Define new collection counter
value_counts = collections.Counter()

# Read raster blocks to build attribute values and counts
print('Building value histogram...')
iteration_start = time.time()
with rasterio.open(wetland_output) as wetland_raster:
    # Find number of raster blocks
    window_list = []
    for block_index, window in wetland_raster.block_windows(1):
        window_list.append(window)
    # Iterate processing through raster blocks
    count = 1
    progress = 0
    for block_index, window in wetland_raster.block_windows(1):
        input_block = wetland_raster.read(1, window=window, masked=True)
        # Use compressed to ignore nodata
        input_data = input_block.compressed()
        if input_data.size == 0:
            # Report progress
            count, progress = raster_block_progress(100, len(window_list), count, progress)
        else:
            # Update the histogram incrementally
            value_counts.update(input_data.tolist())
            # Report progress
            count, progress = raster_block_progress(100, len(window_list), count, progress)
end_timing(iteration_start)

# Raise error for empty output
if not value_counts:
    raise RuntimeError('Raster contains no valid data.')

# Convert counter to sorted lists
print('Building raster attribute table...')
unique_values = sorted(value_counts.keys())
counts = [value_counts[v] for v in unique_values]

# Define DBF table fields
attribute_table = dbf.Table(
    attribute_output,
    'VALUE N(10,0); COUNT N(20,0); LABEL C(64)'
)

# Write attribute table
attribute_table.open(mode=dbf.READ_WRITE)
for value in unique_values:
    count = value_counts[value]
    label = value_labels.get(int(value), "")
    attribute_table.append((int(value), int(count), label))
attribute_table.close()

#### CREATE COLOR MAP
####____________________________________________________

# Create dictionary of value hex colors
value_colors = {
    1: '7C5C5C',
    2: '37B024',
    3: '0F5F2E',
    4: 'CAE925',
    5: '3789D5',
    6: 'FFFFFF',
    7: 'D4BE8A'
}

# Specify colormap file path
colormap_output = wetland_output + '.clr'
if os.path.exists(colormap_output):
    os.remove(colormap_output)

# Write colormap
print('Writing colormap...')
with open(colormap_output, 'w') as f:
    for value, hex_color in value_colors.items():
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        f.write(f'{value} {r} {g} {b}\n')
    f.write('END\n')
