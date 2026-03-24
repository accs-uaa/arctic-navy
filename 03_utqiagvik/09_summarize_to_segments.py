# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Summarize to segments
# Author: Timm Nawrocki
# Last Updated: 2026-03-23
# Usage: Must be executed in a Python 3.12+ installation.
# Description: 'Summarize to segments' resamples the raster to a 2 m resolution, summarizes to image segments, and re-scales the output to 1:10,000.
# ---------------------------------------------------------------------------

# Define region
region = 'Utqiagvik'

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

# Define heterogeneity threshold to determine polygonal complexes
heterogeneity_threshold = 0.1

#### SET UP DIRECTORIES AND FILES
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
repository_folder = os.path.join(drive, root_folder, 'Repositories/arctic-navy')
segment_folder = os.path.join(project_folder, 'Data_Output/segment_data')
input_folder = os.path.join(project_folder, 'Data_Output/vegetation_data/unprocessed')
output_folder = os.path.join(project_folder, 'Data_Output/vegetation_data/processed')

# Define input datasets
area_input = os.path.join(project_folder, f'Data_Input/rasterized_data/{region}_StudyArea_2m_3338.tif')
segment_input = os.path.join(segment_folder, f'{region}_Segments_2m_3338.tif')
vegetation_input = os.path.join(input_folder, f'{region}_Vegetation_0.5m_3338.tif')
label_input = os.path.join(repository_folder, 'value_labels.json')
color_input = os.path.join(repository_folder, 'value_colors.json')

# Define output datasets
vegetation_output = os.path.join(output_folder, f'{region}_Vegetation_900mmu_2m_3338.tif')

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
    veg_array = veg_raster.read(1)
    veg_shape = (veg_raster.height, veg_raster.width)
    veg_bounds = veg_raster.bounds

# Load segment raster data
with rasterio.open(segment_input) as segment_raster:
    # Calculate windows for each resolution
    area_window = from_bounds(*area_bounds, transform=segment_raster.transform) # 2 m
    veg_window = from_bounds(*veg_bounds, transform=segment_raster.transform) # 0.5 m

    # Read the segment data using the calculated geographic windows at 2 m resolution
    segment_2m_array = segment_raster.read(
        1,
        window=area_window,
        out_shape=area_shape,
        resampling=Resampling.nearest,
        boundless=True,
        fill_value=nodata_value
    )

    # Read the segment data using the calculated geographic windows at 0.5 m resolution
    segment_array = segment_raster.read(
        1,
        window=veg_window,
        out_shape=veg_shape,
        resampling=Resampling.nearest,
        boundless=True,
        fill_value=nodata_value
    )
end_timing(start_time)

#### CALCULATE SEGMENT STATISTICS
####____________________________________________________
print('Calculating majority vegetation type per segment...')
start_time = time.time()

# Flatten arrays to 1 dimension for comparison
seg_flat = segment_array.flatten()
veg_flat = veg_array.flatten()

# Combine 1-dimensional arrays into a single 64-bit integer array
combined_flat = (seg_flat.astype(np.uint64) << 8) | veg_flat.astype(np.uint64)

# Count occurrences of every unique combination of segment ID and vegetation type
unique_combos, counts = np.unique(combined_flat, return_counts=True)

# Extract the segment IDs and vegetation types from the combined count array
seg_ids = (unique_combos >> 8).astype(np.int32)
veg_ids = (unique_combos & 0xFF).astype(np.uint8)

# Sort by segment ID and count (ascending)
sort_idx = np.lexsort((counts, seg_ids))

# Reverse arrays so the majority vegetation type is first for each segment
rev_seg = seg_ids[sort_idx][::-1]
rev_veg = veg_ids[sort_idx][::-1]
rev_counts = counts[sort_idx][::-1]

# Return the majority vegetation type and its pixel count for each segment ID
_, unique_idx = np.unique(rev_seg, return_index=True)
majority_seg_ids = rev_seg[unique_idx]
majority_veg_ids = rev_veg[unique_idx]
majority_counts = rev_counts[unique_idx]

# Calculate total 0.5 m pixels per segment
total_seg_ids, total_seg_counts = np.unique(seg_flat, return_counts=True)

# Sort both arrays by segment ID so they align mathematically row-by-row
sort_maj = np.argsort(majority_seg_ids)
maj_seg_sorted = majority_seg_ids[sort_maj]
maj_counts_sorted = majority_counts[sort_maj]

sort_tot = np.argsort(total_seg_ids)
tot_counts_sorted = total_seg_counts[sort_tot]

# Calculate Heterogeneity Index (0.0 = pure, 1.0 = highly mixed)
segment_heterogeneity = (tot_counts_sorted - maj_counts_sorted) / tot_counts_sorted
end_timing(start_time)

#### ASSIGN VEGETATION TYPES TO SEGMENTS
####____________________________________________________
print('Assigning vegetation types to the 2 m segments...')
start_time = time.time()

# Identify valid data region
valid_mask = (area_array == 1)
valid_segment_ids = segment_2m_array[valid_mask]

# Sort majority arrays for binary search
sort_idx = np.argsort(majority_seg_ids)
sorted_seg_ids = majority_seg_ids[sort_idx]
sorted_veg_ids = majority_veg_ids[sort_idx]

# Find the matching index for each segment ID in sorted list
match_indices = np.searchsorted(sorted_seg_ids, valid_segment_ids)
match_indices = np.clip(match_indices, 0, len(sorted_seg_ids) - 1)

# Verify that the ID actually matched and assign values
is_match = sorted_seg_ids[match_indices] == valid_segment_ids
mapped_veg_values = np.full(valid_segment_ids.shape, nodata_value, dtype=np.uint8)
mapped_veg_values[is_match] = sorted_veg_ids[match_indices[is_match]]

# Initialize the final 2 m vegetation array and apply mapped values
rescaled_array = np.full(segment_2m_array.shape, nodata_value, dtype=np.uint8)
rescaled_array[valid_mask] = mapped_veg_values

# Map segment heterogeneity to the valid segment IDs
print('\tAssigning heterogeneity to the 2 m segments...')
match_indices_het = np.searchsorted(maj_seg_sorted, valid_segment_ids)
match_indices_het = np.clip(match_indices_het, 0, len(maj_seg_sorted) - 1)
is_match_het = maj_seg_sorted[match_indices_het] == valid_segment_ids
het_values = np.zeros(valid_segment_ids.shape, dtype=np.float32)
het_values[is_match_het] = segment_heterogeneity[match_indices_het[is_match_het]]
heterogeneity_2m_array = np.zeros(segment_2m_array.shape, dtype=np.float32)
heterogeneity_2m_array[valid_mask] = het_values

# Isolate segments exceeding the threshold
is_complex = heterogeneity_2m_array > heterogeneity_threshold

# Reclassify polygonal complexes directly on the rescaled_array
print('\tRe-classifying polygonal complexes based on heterogeneity...')
rescaled_array = np.where(is_complex & (rescaled_array == 145),
                          140, rescaled_array) # tussock
rescaled_array = np.where(is_complex & np.isin(rescaled_array, [147, 152]),
                          139, rescaled_array) # non-tussock
rescaled_array = np.where(is_complex & np.isin(rescaled_array, [142, 143]),
                          180, rescaled_array) # peatland
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
coastal_mask = np.isin(rescaled_array, coastal_list)
wet_mask = np.isin(rescaled_array, wet_list)
omitted_mask = np.isin(rescaled_array, omitted_list)
mesic_mask = ~(coastal_mask | wet_mask | omitted_mask | (rescaled_array == nodata_value))
end_timing(start_time)

# Parse functional types
coastal_sieve = apply_sieve(coastal_mask, rescaled_array, nodata_value, mmu_pixels=25)
wet_sieve = apply_sieve(wet_mask, rescaled_array, nodata_value, mmu_pixels=25)
mesic_sieve = apply_sieve(mesic_mask, rescaled_array, nodata_value, mmu_pixels=25)
end_timing(start_time)

#### FINAL MERGE & FILTER
####____________________________________________________
print('Merging rasters...')
start_time = time.time()

# Merge rasters
merged_array = np.where(coastal_sieve != nodata_value, coastal_sieve,
                        np.where(wet_sieve != nodata_value, wet_sieve,
                                 np.where(mesic_sieve != nodata_value, mesic_sieve, nodata_value)))

# Enforce mmu on the merged raster
print('\tConducting final sieve iterations on merged data...')
final_sieve = features.sieve(merged_array, size=36, connectivity=8)
final_sieve = features.sieve(final_sieve, size=64, connectivity=8)
final_sieve = features.sieve(final_sieve, size=100, connectivity=8)
final_sieve = features.sieve(final_sieve, size=144, connectivity=8)
final_sieve = features.sieve(final_sieve, size=225, connectivity=8)

# Fill no data using a categorical nibble
print('\tFilling no data...')
final_nibble = categorical_nibble(final_sieve, nodata_value)

# Generalize the raster shapes with majority filter
print('\tApplying majority filter...')
final_array = apply_majority_filter(final_nibble, nodata_value)

# Add omitted data into final raster
print('\tAdding omitted data...')
final_array = np.where(omitted_mask, rescaled_array, final_array)

# Extract to study area
print('\tExtracting to study area...')
final_array = np.where(area_array == 1, final_array, nodata_value)

# Update the input metadata dictionary for the output export
output_profile.update(dtype=rasterio.uint8,
                      count=1,
                      nodata=nodata_value,
                      compress='lzw')

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
colormap_output = vegetation_output + '.clr'
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
