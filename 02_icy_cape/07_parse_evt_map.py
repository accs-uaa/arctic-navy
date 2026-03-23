# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Parse EVT map 1:2,500 scale
# Author: Timm Nawrocki
# Last Updated: 2026-03-21
# Usage: Must be executed in a Python 3.12+ installation.
# Description: "Parse EVT map 1:2,500 scale" implements a programmatic key to creat an existing vegetation type map at 1:2,500 scale based on surficial features, foliar cover, and ancillary data.
# ---------------------------------------------------------------------------

# Define region
region = 'IcyCape'

# Import packages
import os
import time
import numpy as np
import rasterio
from rasterio.warp import Resampling
from rasterio.windows import from_bounds
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
input_folder = os.path.join(project_folder, 'Data_Input/rasterized_data')
distance_folder = os.path.join(project_folder, 'Data_Input/distance_data/processed')
foliar_folder = os.path.join(project_folder, 'Data_Output/foliar_data')
surficial_folder = os.path.join(project_folder, 'Data_Output/surficial_data')
output_folder = os.path.join(project_folder, 'Data_Output/vegetation_data')

# Define input files
area_input = os.path.join(input_folder, f'{region}_StudyArea_0.5m_3338.tif')
surficial_input = os.path.join(surficial_folder, f'{region}_Surficial_0.5m_3338.tif')
dryas_input = os.path.join(foliar_folder, f'{region}_dryas_0.5m_3338.tif')
dsalix_input = os.path.join(foliar_folder, f'{region}_dsalix_0.5m_3338.tif')
erivag_input = os.path.join(foliar_folder, f'{region}_erivag_0.5m_3338.tif')
halgra_input = os.path.join(foliar_folder, f'{region}_halgra_0.5m_3338.tif')
nerishr_input = os.path.join(foliar_folder, f'{region}_nerishr_0.5m_3338.tif')
sphagn_input = os.path.join(foliar_folder, f'{region}_sphagn_0.5m_3338.tif')
wetsed_input = os.path.join(foliar_folder, f'{region}_wetsed_0.5m_3338.tif')
water_input = os.path.join(foliar_folder, f'{region}_watercor_0.5m_3338.tif')
coastal_input = os.path.join(input_folder, f'{region}_CoastalZone_0.5m_3338.tif')
infrastructure_input = os.path.join(input_folder, f'{region}_Infrastructure_0.5m_3338.tif')
disturbed_input = os.path.join(input_folder, f'{region}_Correction_Disturbed_0.5m_3338.tif')
watercor_input = os.path.join(input_folder, f'{region}_Correction_Water_0.5m_3338.tif')
saltcor_input = os.path.join(input_folder, f'{region}_Correction_SaltIntruded_0.5m_3338.tif')
tidalcor_input = os.path.join(input_folder, f'{region}_Correction_TidalMarsh_0.5m_3338.tif')
coastcor_input = os.path.join(input_folder, f'{region}_Correction_Coast_0.5m_3338.tif')

# Define output file
vegetation_output = os.path.join(output_folder, f'{region}_Vegetation_0.5m_3338.tif')

#### PARSE EXISTING VEGETATION TYPES
####____________________________________________________

# Prepare input rasters
area_raster = rasterio.open(area_input)
surficial_raster = rasterio.open(surficial_input)
dryas_raster = rasterio.open(dryas_input)
dsalix_raster = rasterio.open(dsalix_input)
erivag_raster = rasterio.open(erivag_input)
halgra_raster = rasterio.open(halgra_input)
nerishr_raster = rasterio.open(nerishr_input)
sphagn_raster = rasterio.open(sphagn_input)
wetsed_raster = rasterio.open(wetsed_input)
water_raster = rasterio.open(water_input)
coastal_raster = rasterio.open(coastal_input)
infrastructure_raster = rasterio.open(infrastructure_input)
disturbed_raster = rasterio.open(disturbed_input)
watercor_raster = rasterio.open(watercor_input)
saltcor_raster = rasterio.open(saltcor_input)
tidalcor_raster = rasterio.open(tidalcor_input)
coastcor_raster = rasterio.open(coastcor_input)

# Prepare output profile
output_profile = area_raster.profile.copy()
output_profile.update({
    'height': area_raster.height,
    'width': area_raster.width,
    'transform': area_raster.transform,
    'crs': area_raster.crs,
    'nodata': nodata_value,
    'dtype': 'uint8',
    'compress': 'lzw',
    'bigtiff': 'NO',
    'tiled': True,
    'blockxsize': 256,
    'blockysize': 256
})

# Define a function to read raster block
def read_raster_block(input_raster, window_bounds):
    input_window = from_bounds(
        *window_bounds,
        transform=input_raster.transform).round_offsets().round_lengths()
    output_block = input_raster.read(1, window=input_window, masked=False)
    return output_block

# Parse foliar cover
print(f'Parsing foliar cover to types...')
iteration_start = time.time()
with (rasterio.open(vegetation_output, 'w', **output_profile) as dst):
    # Find number of raster blocks
    window_list = []
    for block_index, window in area_raster.block_windows(1):
        window_list.append(window)
    # Iterate processing through raster blocks
    count = 1
    progress = 0
    for block_index, window in area_raster.block_windows(1):
        #### LOAD BLOCKS

        # Load area block
        area_block = area_raster.read(1, window=window, masked=False)

        # Compute bounds of the current output window
        window_bounds = rasterio.windows.bounds(window, area_raster.transform)

        # Load raster blocks
        surficial_block = read_raster_block(surficial_raster, window_bounds)
        dryas_block = read_raster_block(dryas_raster, window_bounds)
        dsalix_block = read_raster_block(dsalix_raster, window_bounds)
        erivag_block = read_raster_block(erivag_raster, window_bounds)
        halgra_block = read_raster_block(halgra_raster, window_bounds)
        nerishr_block = read_raster_block(nerishr_raster, window_bounds)
        sphagn_block = read_raster_block(sphagn_raster, window_bounds)
        wetsed_block = read_raster_block(wetsed_raster, window_bounds)
        water_block = read_raster_block(water_raster, window_bounds)
        coastal_block = read_raster_block(coastal_raster, window_bounds)
        infrastructure_block = read_raster_block(infrastructure_raster, window_bounds)
        disturbed_block = read_raster_block(disturbed_raster, window_bounds)
        watercor_block = read_raster_block(watercor_raster, window_bounds)
        saltcor_block = read_raster_block(saltcor_raster, window_bounds)
        tidalcor_block = read_raster_block(tidalcor_raster, window_bounds)
        coastcor_block = read_raster_block(coastcor_raster, window_bounds)

        #### CORRECT SURFICIAL FEATURES

        # Correct water
        surficial_block = np.where(watercor_block == 1, 1, surficial_block)

        # Correct salt-intruded
        surficial_block = np.where((saltcor_block == 1) & (np.isin(surficial_block, [4, 6])),
                                   7, surficial_block)

        # Correct wet
        surficial_block = np.where((surficial_block == 2) & (wetsed_block >= 20),
                                   3, surficial_block)

        # Correct tidal marsh
        surficial_block = np.where((surficial_block == 5)
                                   & (coastal_block != 1),
                                   3, surficial_block)

        # Correct beach
        surficial_block = np.where((surficial_block == 6)
                                   & (coastal_block != 1),
                                   2, surficial_block)

        # Correct barren
        surficial_block = np.where((surficial_block == 4)
                                   & (coastal_block != 1)
                                   & (coastcor_block == 1),
                                   2, surficial_block)

        #### COASTAL TYPES

        # 0. Initiate out_block
        out_block = np.where(area_block == 1, 0, area_block)

        # 161. Salt-intruded Tundra
        out_block = np.where((out_block == 0)
                             & (surficial_block == 7),
                             161, out_block)

        # 162. Arctic Coastal Dwarf Willow Graminoid
        out_block = np.where((out_block == 0)
                             & (np.isin(surficial_block, [4, 5, 6]))
                             & (coastal_block == 1)
                             & (dsalix_block >= 7)
                             & (tidalcor_block != 1),
                             162, out_block)

        # 163. Arctic Coastal Salt Marsh
        out_block = np.where((out_block == 0)
                             & ((surficial_block == 5) | (dsalix_block >= 7))
                             & (coastal_block == 1),
                             163, out_block)

        # 158. Arctic Coastal & Estuarine Barren
        out_block = np.where((out_block == 0)
                             & (surficial_block == 4)
                             & (coastal_block == 1),
                             158, out_block)

        # 160. Arctic Herbaceous Coastal Beach
        out_block = np.where((out_block == 0)
                             & (surficial_block == 6)
                             & (coastal_block == 1),
                             160, out_block)

        #### MESIC TYPES

        # 152. Arctic Ericaceous(-Dryas-Willow) Dwarf Shrub
        out_block = np.where((out_block == 0)
                             & (surficial_block == 2)
                             & ((dryas_block >= 4) | (nerishr_block >= 4))
                             & (erivag_block < 7),
                             152, out_block)

        # 145. Arctic tussock dwarf shrub tundra
        out_block = np.where((out_block == 0)
                             & (surficial_block == 2)
                             & (erivag_block >= 7),
                             145, out_block)

        # 147. Arctic Herbaceous Non-tussock Tundra
        out_block = np.where((out_block == 0)
                             & (surficial_block == 2),
                             147, out_block)

        #### WET TYPES

        # 170. Arctic Freshwater Marsh
        out_block = np.where((out_block == 0)
                             & ((surficial_block == 3) | (surficial_block == 1))
                             & (coastal_block != 1)
                             & (water_block >= 20)
                             & (wetsed_block >= 10)
                             & (sphagn_block < 5),
                             170, out_block)

        # 142. Arctic Sphagnum-Sedge Peatland, Ombrotrophic
        out_block = np.where((out_block == 0)
                             & (surficial_block == 3)
                             & (sphagn_block >= 5),
                             142, out_block)

        # 143. Arctic Brown Moss-Sedge Peatland, Minerotrophic
        out_block = np.where((out_block == 0)
                             & (surficial_block == 3),
                             143, out_block)

        #### CORRECTIONS

        # 156. Arctic Barren & Sparsely Vegetated
        out_block = np.where((out_block == 0)
                             & (surficial_block == 4),
                             156, out_block)

        #### MANUAL MODIFICATIONS

        # 173. Disturbed Vegetation
        out_block = np.where((disturbed_block == 1) & (surficial_block != 1),
                             173, out_block)

        # 174. Infrastructure
        out_block = np.where((infrastructure_block == 1) & (surficial_block != 1),
                             174, out_block)

        # 176. Water
        out_block = np.where(((out_block == 0) & (surficial_block == 1))
                             | (watercor_block == 1),
                             176, out_block)

        #### REVISE NO DATA
        out_block = np.where(out_block == 0, nodata_value, out_block)

        #### WRITE DATA

        # Set no data values from area raster to no data
        out_block = np.where(area_block == 1, out_block, nodata_value)

        # Write results
        dst.write(out_block, 1, window=window)
        # Report progress
        count, progress = raster_block_progress(100, len(window_list), count, progress)
end_timing(iteration_start)

# Close rasters
for raster in [area_raster, surficial_raster, dryas_raster, dsalix_raster, erivag_raster,
               halgra_raster, nerishr_raster, wetsed_raster, water_raster, coastal_raster,
               infrastructure_raster, disturbed_raster, watercor_raster, saltcor_raster,
               tidalcor_raster]:
    raster.close()

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

# Create dictionary of value labels
value_labels = {
    142: 'Arctic Sphagnum-Sedge Peatland, Ombrotrophic',
    143: 'Arctic Brown Moss-Sedge Peatland, Minerotrophic',
    145: 'Arctic Tussock Dwarf Shrub Tundra',
    147: 'Arctic Herbaceous Non-tussock Tundra',
    152: 'Arctic Ericaceous(-Dryas-Willow) Dwarf Shrub',
    156: 'Arctic Barren & Sparsely Vegetated',
    158: 'Arctic Coastal & Estuarine Barren',
    160: 'Arctic Herbaceous Coastal Beach',
    161: 'Arctic Salt-intruded Tundra',
    162: 'Arctic Coastal Dwarf Willow Graminoid',
    163: 'Arctic Coastal Salt Marsh',
    170: 'Arctic Freshwater Marsh',
    173: 'Disturbed Vegetation',
    174: 'Infrastructure',
    176: 'Water'
}

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
    142: '87C58F',
    143: 'B6BF8C',
    145: '730000',
    147: '35CECD',
    152: '3B5D6C',
    156: 'FFEAC2',
    158: 'FFEAC2',
    160: '897044',
    161: '000000',
    162: '7AF5CA',
    163: '00A884',
    170: 'E8BEFF',
    173: 'FFBEBE',
    174: 'FF0000',
    176: 'BEE8FF'
}

# Specify colormap file path
colormap_output = vegetation_output + '.clr'
if os.path.exists(colormap_output):
    os.remove(colormap_output)

# Write colormap
print('Writing colormap...')
with open(colormap_output, 'w') as f:
    for value, hex_color in value_colors.items():
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        f.write(f'{value} {r} {g} {b}\n')
    f.write('END\n')
