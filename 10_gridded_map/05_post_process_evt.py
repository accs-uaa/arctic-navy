# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Post-process EVT
# Author: Timm Nawrocki
# Last Updated: 2026-01-08
# Usage: Execute in Python 3.9+.
# Description: "Post-process EVT" builds pyramids, attribute table, and color map for evt raster.
# ---------------------------------------------------------------------------

# Import packages
import os
import time
import rasterio
from rasterio.warp import Resampling
import collections
import dbf
from akutils import *

# Set nodata value
nodata_value = 255

# Set round date
round_date = 'round_20260123'

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
output_folder = os.path.join(project_folder, 'Data_Output/evt', round_date)

# Define input files
area_input = os.path.join(project_folder, 'Data_Input/ArcticCoastal_MapDomain_10m_3338.tif')

# Define output file
evt_output = os.path.join(output_folder, 'ArcticCoastal_Vegetation_1600mmu_10m_3338.tif')

#### BUILD RASTER PYRAMIDS (OVERVIEWS)
####____________________________________________________

# Define overview levels
overview_levels = [2, 4, 8, 16, 32, 64, 128, 256]

# Build pyramids
print(f'Building pyramids...')
iteration_start = time.time()
with rasterio.open(evt_output, 'r+') as dst:
    # Build pyramids with bilinear resampling
    dst.build_overviews(overview_levels, resampling=Resampling.mode)
    # Update metadata to indicate overviews exist
    dst.update_tags(ns='rio_overview', resampling='mode')
end_timing(iteration_start)

#### BUILD RASTER ATTRIBUTE TABLE
####____________________________________________________

# Create dictionary of value labels
value_labels = {
    1: 'Arctic Coastal & Estuarine Barren',
    2: 'Arctic Herbaceous Coastal Beach',
    3: 'Arctic Herbaceous & Shrub Coastal Dune',
    5: 'Arctic Coastal Salt Marsh',
    6: 'Arctic Coastal Dwarf Shrub Graminoid Non-tussock Tundra',
    7: 'Arctic Barren & Sparsely Vegetated Floodplain',
    8: 'Arctic Herbaceous Floodplain',
    9: 'Arctic Willow Floodplain',
    10: 'Arctic Alder(-Willow) Floodplain',
    11: 'Arctic Freshwater Marsh',
    12: 'Arctic Wet Meadow (Floodplain/Mineral)',
    13: 'Arctic Herbaceous Inland Dune',
    14: 'Arctic Willow Inland Dune',
    15: 'Arctic Dryas(-Willow) Floodplain',
    16: 'Arctic Willow Low Shrub',
    18: 'Arctic Birch(-Willow) Shrub',
    19: 'Arctic Alder(-Willow) Shrub',
    20: 'Arctic Ericaceous(-Dryas) Dwarf Shrub',
    21: 'Arctic Dryas(-Willow) Dwarf Shrub',
    22: 'Arctic Tussock Low Shrub Tundra',
    24: 'Arctic Tussock Dwarf Shrub Tundra',
    26: 'Arctic Herbaceous Non-tussock Tundra',
    28: 'Arctic Sphagnum-Sedge Peatland, Ombrotrophic',
    29: 'Arctic Brown Moss-Sedge Peatland, Minerotrophic',
    30: 'Arctic Shrub-Sedge Peatland, Ombrotrophic',
    31: 'Arctic Shrub-Sedge Peatland, Minerotrophic',
    32: 'Arctic Tussock Tundra (Mesic) Polygonal Complex',
    33: 'Arctic Non-tussock (Mesic) Polygonal Complex',
    34: 'Arctic Peatland (Wet) Polygonal Complex',
    36: 'Arctic Barren & Sparsely Vegetated',
    38: 'Persistent Waterbody',
    39: 'Infrastructure',
    40: 'Disturbed Tundra'
}

# Specify attribute table file path
attribute_output = evt_output + '.vat.dbf'
if os.path.exists(attribute_output):
    os.remove(attribute_output)

# Define new collection counter
value_counts = collections.Counter()

# Read raster blocks to build attribute values and counts
print('Building value histogram...')
iteration_start = time.time()
with rasterio.open(evt_output) as evt_raster:
    # Find number of raster blocks
    window_list = []
    for block_index, window in evt_raster.block_windows(1):
        window_list.append(window)
    # Iterate processing through raster blocks
    count = 1
    progress = 0
    for block_index, window in evt_raster.block_windows(1):
        input_block = evt_raster.read(1, window=window, masked=True)
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
    1: 'FFEAC2',
    2: '897044',
    3: 'B07500',
    5: 'C8F1E5',
    6: 'FFD37F',
    7: 'FFFFBE',
    8: 'D5E600',
    9: 'C5BCD5',
    10: '935B79',
    11: '6A1837',
    12: '59C8A8',
    13: 'CDAA66',
    14: 'FFFF73',
    15: 'A898BE',
    16: 'C668DF',
    18: 'C668DF',
    19: 'C668DF',
    20: '466F81',
    21: '3B5D6C',
    22: 'B14647',
    24: '730000',
    26: '35CECD',
    28: '87C58F',
    29: 'B6BF8C',
    30: '448C4D',
    31: '828D4E',
    32: '942A2A',
    33: '00391F',
    34: '8400A8',
    36: 'CCCCCC',
    38: 'BEE8FF',
    39: 'FF0000',
    40: 'DF9E9E'
}

# Specify colormap file path
colormap_output = evt_output + '.clr'
if os.path.exists(colormap_output):
    os.remove(colormap_output)

# Write colormap
print('Writing colormap...')
with open(colormap_output, 'w') as f:
    for value, hex_color in value_colors.items():
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        f.write(f'{value} {r} {g} {b}\n')
    f.write('END\n')
