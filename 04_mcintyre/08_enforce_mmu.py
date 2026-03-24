# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Enforce minimum mapping unit
# Author: Timm Nawrocki
# Last Updated: 2026-03-23
# Usage: Must be executed in a Python 3.12+ installation.
# Description: 'Enforce minimum mapping unit' removes and replaces map units less than 16 pixels in area.
# ---------------------------------------------------------------------------

# Define region
region = 'McIntyre'

# Import packages
import os
import time
import collections
import dbf
import json
import numpy as np
import rasterio
from rasterio import features
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from scipy import stats
from scipy.ndimage import distance_transform_edt
from akutils import *

# Define nodata value
nodata_value = 255

#### SET UP DIRECTORIES AND FILES
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
repository_folder = os.path.join(drive, root_folder, 'Repositories/arctic-navy')
rasterized_folder = os.path.join(project_folder, 'Data_Input/rasterized_data')
input_folder = os.path.join(project_folder, 'Data_Output/vegetation_data/unprocessed')
output_folder = os.path.join(project_folder, 'Data_Output/vegetation_data/processed')

# Define input datasets
area_input = os.path.join(rasterized_folder, f'{region}_StudyArea_0.5m_3338.tif')
vegetation_input = os.path.join(input_folder, f'{region}_Vegetation_0.5m_3338.tif')
label_input = os.path.join(repository_folder, 'value_labels.json')
color_input = os.path.join(repository_folder, 'value_colors.json')

# Define output datasets
vegetation_output = os.path.join(output_folder, f'{region}_Vegetation_2mmu_0.5m_3338.tif')

#### DEFINE FUNCTIONS
####____________________________________________________

def apply_sieve(target_mask, type_array, nodata_value, mmu_pixels=8):
    # Isolate target data
    isolated_array = np.where(target_mask, type_array, nodata_value)

    # Apply Sieve Filter (see GDAL Sieve)
    sieve_array = features.sieve(isolated_array, size=mmu_pixels, connectivity=8)

    return sieve_array

def apply_majority_filter(input_array, nodata_value):
    # Pad array by 1 pixel on all sides to prevent edge data loss
    padded = np.pad(input_array, pad_width=1, mode='constant', constant_values=nodata_value)

    # Extract the 8 neighbors by shifting in eight directions
    n1 = padded[0:-2, 0:-2] # NW
    n2 = padded[0:-2, 1:-1] # N
    n3 = padded[0:-2, 2:] # NE
    n4 = padded[1:-1, 0:-2] # W
    n6 = padded[1:-1, 2:] # E
    n7 = padded[2:, 0:-2] # SW
    n8 = padded[2:, 1:-1] # S
    n9 = padded[2:, 2:] # SE

    # Stack the 8 neighbor arrays into a block
    neighbors = np.stack([n1, n2, n3, n4, n6, n7, n8, n9], axis=0)

    # Calculate the most frequent neighbor value and the number of times it appears
    mode_result = stats.mode(neighbors, axis=0, keepdims=False)

    # Replace the original pixel with the majority value if 5 or more neighbors share it
    replace_mask = (mode_result.count >= 5)
    filtered_array = np.where(replace_mask, mode_result.mode, input_array)

    return filtered_array

def categorical_nibble(input_array, nodata_val):
    # Create a boolean mask of the valid data
    valid_mask = (input_array != nodata_val)

    # If the array is entirely nodata or has no nodata, return as is
    if not valid_mask.any() or valid_mask.all():
        return input_array.copy()

    # Return indices of the nearest valid pixels
    _, indices = distance_transform_edt(~valid_mask, return_indices=True)

    # Map the nearest valid values to the entire array
    nibbled_array = input_array[tuple(indices)]

    return nibbled_array

#### LOAD RASTER DATA
####____________________________________________________
print('Loading rasters into memory...')
start_time = time.time()

# Load area raster data
with rasterio.open(area_input) as area_raster:
    area_array = area_raster.read(1)
    area_shape = (area_raster.height, area_raster.width)
    area_bounds = area_raster.bounds
    output_profile = area_raster.profile

# Load vegetation raster data
with rasterio.open(vegetation_input) as veg_raster:
    # Calculate windows for each resolution
    area_window = from_bounds(*area_bounds, transform=veg_raster.transform)  # 0.5 m

    # Read the vegetation data using the calculated geographic windows at 0.5 m resolution
    veg_array = veg_raster.read(
        1,
        window=area_window,
        out_shape=area_shape,
        resampling=Resampling.nearest,
        boundless=True,
        fill_value=nodata_value
    )
end_timing(start_time)

#### PARSE FUNCTIONAL TYPES
####____________________________________________________
print('Processing functional splits...')
start_time = time.time()

# Define Functional Types
coastal_list = [158, 159, 160, 161, 162, 163]
wet_list = [142, 143, 170, 171, 180]
omitted_list = [173, 174, 176]

# Create masks
coastal_mask = np.isin(veg_array, coastal_list)
wet_mask = np.isin(veg_array, wet_list)
omitted_mask = np.isin(veg_array, omitted_list)
mesic_mask = ~(coastal_mask | wet_mask | omitted_mask | (veg_array == nodata_value))
end_timing(start_time)

# Parse functional types
coastal_sieve = apply_sieve(coastal_mask, veg_array, nodata_value, mmu_pixels=4)
wet_sieve = apply_sieve(wet_mask, veg_array, nodata_value, mmu_pixels=4)
mesic_sieve = apply_sieve(mesic_mask, veg_array, nodata_value, mmu_pixels=4)
end_timing(start_time)

#### FINAL MERGE & FILTER
####____________________________________________________
print('Merging rasters...')
start_time = time.time()

# Merge functional types
merged_array = np.where(coastal_sieve != nodata_value, coastal_sieve,
                        np.where(wet_sieve != nodata_value, wet_sieve,
                                 np.where(mesic_sieve != nodata_value, mesic_sieve, nodata_value)))

# Enforce mmu on the merged raster
print('\tConducting final sieve and nibble on merged data...')
final_sieve = features.sieve(merged_array, size=6, connectivity=8)
final_sieve = features.sieve(final_sieve, size=8, connectivity=8)

# Fill no data using a categorical nibble
print('\tFilling no data...')
final_nibble = categorical_nibble(final_sieve, nodata_value)

# Generalize the raster shapes with majority filter
print('\tApplying majority filter...')
final_array = apply_majority_filter(final_nibble, nodata_value)

# Add omitted data into final raster
print('\tAdding omitted data...')
final_array = np.where(omitted_mask, veg_array, final_array)

# Extract to study area
print('\tExtracting to study area...')
final_array = np.where(area_array == 1, final_array, nodata_value)

# Update the input metadata dictionary for the output export
output_profile.update(
    dtype=rasterio.uint8,
    count=1,
    nodata=nodata_value,
    compress='lzw'
)

# Export final raster
print('\tExporting vegetation raster...')
with rasterio.open(vegetation_output, 'w', **output_profile) as out_raster:
    out_raster.write(final_array, 1)
end_timing(start_time)

#### BUILD RASTER PYRAMIDS (OVERVIEWS)
####____________________________________________________

# Define overview levels
overview_levels = [2, 4, 8, 16, 32, 64, 128, 256]

# Build pyramids
print(f'Building pyramids...')
iteration_start = time.time()
with rasterio.open(vegetation_output, 'r+') as dst:
    # Build pyramids with bilinear resampling
    dst.build_overviews(overview_levels, resampling=Resampling.mode)
    # Update metadata to indicate overviews exist
    dst.update_tags(ns='rio_overview', resampling='mode')
end_timing(iteration_start)

#### BUILD RASTER ATTRIBUTE TABLE
####____________________________________________________

# Specify attribute table file path
attribute_output = vegetation_output + '.vat.dbf'
if os.path.exists(attribute_output):
    os.remove(attribute_output)

# Define new collection counter
value_counts = collections.Counter()

# Read raster blocks to build attribute values and counts
print('Building value histogram...')
iteration_start = time.time()
with rasterio.open(vegetation_output) as evt_raster:
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

# Load the JSON label data
with open(label_input, 'r') as f:
    raw_labels = json.load(f)
value_labels = {
    int(k): v for k, v in raw_labels.items() if int(k) in unique_values
}

# Write attribute table
attribute_table.open(mode=dbf.READ_WRITE)
for value in unique_values:
    count = value_counts[value]
    label = value_labels.get(int(value), "")
    attribute_table.append((int(value), int(count), label))
attribute_table.close()

#### CREATE COLOR MAP
####____________________________________________________

# Specify colormap file path
colormap_output = os.path.splitext(vegetation_output)[0] + '.clr'
if os.path.exists(colormap_output):
    os.remove(colormap_output)

# Load the JSON color data
with open(color_input, 'r') as f:
    raw_colors = json.load(f)
value_colors = {
    int(k): v for k, v in raw_colors.items() if int(k) in unique_values
}

# Write colormap
print('Writing colormap...')
with open(colormap_output, 'w') as f:
    for value, hex_color in value_colors.items():
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        f.write(f'{value} {r} {g} {b}\n')
    f.write('END\n')
