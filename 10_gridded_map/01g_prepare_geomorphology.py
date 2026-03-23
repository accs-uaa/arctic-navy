# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Prepare geomorphology data
# Author: Timm Nawrocki
# Last Updated: 2026-01-06
# Usage: Execute in Python 3.9+.
# Description: "Prepare geomorphology data" extracts Arctic Coastal Plain Geomorphology raster to common extent, mask, grid, and cell size.
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
geomorph_input = os.path.join(input_folder, 'NorthernAlaska_CoastalPlain_Geomorphology.tif')

# Define output file
geomorph_output = os.path.join(output_folder, 'ArcticCoastal_Geomorphology_10m_3338.tif')

#### PROCESS RASTER EXTRACTION
####____________________________________________________

# Read input rasters
area_raster = rasterio.open(area_input)
geomorph_raster = rasterio.open(geomorph_input)

# Prepare output profile
output_profile = geomorph_raster.profile.copy()
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

# Reproject and extract raster to area
print(f'Reprojecting and extracting input raster to area...')
print(f'Source CRS: {geomorph_raster.crs}')
print(f'Target CRS: {area_raster.crs}')
iteration_start = time.time()
with rasterio.open(geomorph_output, 'w', **output_profile) as dst:
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
            source=rasterio.band(geomorph_raster, 1),
            destination=out_block,
            src_transform=geomorph_raster.transform,
            src_crs=geomorph_raster.crs,
            dst_transform=dst_window_transform,
            dst_crs=area_raster.crs,
            resampling=Resampling.nearest,
            src_nodata=geomorph_raster.nodata,
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
with rasterio.open(geomorph_output, 'r+') as dst:
    # Build pyramids with bilinear resampling
    dst.build_overviews(overview_levels, resampling=Resampling.mode)
    # Update metadata to indicate overviews exist
    dst.update_tags(ns='rio_overview', resampling='mode')
end_timing(iteration_start)

#### BUILD RASTER ATTRIBUTE TABLE
####____________________________________________________

# Create dictionary of value labels
value_labels = {
    2: 'Coalescent Low-center Polygons',
    3: 'Low-center Polygons',
    4: 'Non-patterned Drained Thaw Lake Basins',
    7: 'Drained Slope',
    8: 'Flat-center Polygons',
    9: 'High-center Polygons',
    10: 'Sandy Barrens',
    11: 'Sand Dunes',
    12: 'Ice',
    13: 'Coastal Saline Waters',
    16: 'Rivers',
    17: 'Developed',
    18: 'Riparian Corridors',
    20: 'Ponds',
    21: 'Small Lakes',
    22: 'Medium Lakes',
    23: 'Large Lakes'
}

# Specify attribute table file path
attribute_output = geomorph_output + '.vat.dbf'
if os.path.exists(attribute_output):
    os.remove(attribute_output)

# Define new collection counter
value_counts = collections.Counter()

# Read raster blocks to build attribute values and counts
print('Building value histogram...')
iteration_start = time.time()
with rasterio.open(geomorph_output) as geomorph_raster:
    # Find number of raster blocks
    window_list = []
    for block_index, window in geomorph_raster.block_windows(1):
        window_list.append(window)
    # Iterate processing through raster blocks
    count = 1
    progress = 0
    for block_index, window in geomorph_raster.block_windows(1):
        input_block = geomorph_raster.read(1, window=window, masked=True)
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
    2: '00D600',
    3: 'B0FF78',
    4: '008F00',
    7: 'CC2400',
    8: 'FFDB00',
    9: 'FFA100',
    10: '874500',
    11: 'FFFF00',
    12: 'EDFFFF',
    13: '000875',
    16: '78FFEF',
    17: '000000',
    18: '96B000',
    20: 'C4CDFF',
    21: '8A97FF',
    22: '4F78FF',
    23: '0000D1'
}

# Specify colormap file path
colormap_output = geomorph_output + '.clr'
if os.path.exists(colormap_output):
    os.remove(colormap_output)

# Write colormap
print('Writing colormap...')
with open(colormap_output, 'w') as f:
    for value, hex_color in value_colors.items():
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        f.write(f'{value} {r} {g} {b}\n')
    f.write('END\n')
