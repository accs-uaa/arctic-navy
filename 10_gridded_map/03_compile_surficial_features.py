# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Compile surficial features
# Author: Timm Nawrocki
# Last Updated: 2026-01-24
# Usage: Execute in Python 3.9+.
# Description: "Compile surficial features" compiles mutually exclusive surficial features (e.g., not floodplains) into a single raster.
# ---------------------------------------------------------------------------

# Import packages
import os
import time
import numpy as np
import rasterio
from rasterio.warp import Resampling
import collections
import dbf
from akutils import *

# Set no data
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
ancillary_folder = os.path.join(project_folder, 'Data_Input/ancillary_data')
output_folder = os.path.join(project_folder, 'Data_Output/surficial_features', round_date)

# Define input files
area_input = os.path.join(project_folder, 'Data_Input/ArcticCoastal_MapDomain_10m_3338.tif')
wetland_input = os.path.join(ancillary_folder,
                             'Panarctic_Wetlands_10m/processed',
                             'ArcticCoastal_PanarcticWetland_v1.0_10m_3338.tif')
esa_input = os.path.join(ancillary_folder,
                         'ESA_WorldCover_10m/processed',
                         'ArcticCoastal_ESAWorldCover2_10m_3338.tif')
esri_input = os.path.join(ancillary_folder,
                          'ESRI_LandCover_10m/processed',
                          'ArcticCoastal_ESRILandCover_10m_3338.tif')
landfire_input = os.path.join(ancillary_folder,
                              'Landfire_2023_EVT_30m/processed',
                              'ArcticCoastal_Landfire_10m_3338.tif')
geomorph_input = os.path.join(ancillary_folder,
                              'ArcticCoastal_Geomorphology_30m/processed',
                              'ArcticCoastal_Geomorphology_10m_3338.tif')
barren_input = os.path.join(ancillary_folder,
                            'ArcticCoastal_Geomorphology_30m/processed',
                            'ArcticCoastal_Barren_10m_3338.tif')
coastal_input = os.path.join(ancillary_folder,
                             'Coastal_Zone_10m/processed',
                             'ArcticCoastal_Coastal_10m_3338.tif')
dune_input = os.path.join(ancillary_folder,
                          'ArcticCoastal_Geomorphology_30m/processed',
                          'ArcticCoastal_Dunes_10m_3338.tif')
sand_input = os.path.join(ancillary_folder,
                              'ArcticCoastal_Geomorphology_30m/processed',
                              'ArcticCoastal_SandSheet_Generalized_10m_3338.tif')
sachi_input = os.path.join(ancillary_folder,
                           'Infrastructure_Coastal_10m/processed',
                           'ArcticCoastal_Infrastructure_v2.0_10m_3338.tif')
nssi_input = os.path.join(ancillary_folder,
                          'Infrastructure_NSSI/processed',
                          'ArcticCoastal_Infrastructure_10m_3338.tif')
ecotype_input = os.path.join(ancillary_folder,
                             'ABR_Shell_Ecotypes_30m/processed',
                             'ArcticCoastal_Ecotypes_10m_3338.tif')
gmt2_input = os.path.join(ancillary_folder,
                          'GMT2_SurficialFeatures_2m/processed',
                          'ArcticCoastal_GMT2_Surficial_10m_3338.tif')
water_input = os.path.join(ancillary_folder,
                           'Manual_Water_10m/processed',
                           'ArcticCoastal_ManualWater_10m_3338.tif')

# Define output file
surficial_output = os.path.join(output_folder, 'ArcticCoastal_SurficialFeatures_10m_3338.tif')

# Read input rasters
area_raster = rasterio.open(area_input)
wetland_raster = rasterio.open(wetland_input)
esa_raster = rasterio.open(esa_input)
esri_raster = rasterio.open(esri_input)
landfire_raster = rasterio.open(landfire_input)
geomorph_raster = rasterio.open(geomorph_input)
barren_raster = rasterio.open(barren_input)
coastal_raster = rasterio.open(coastal_input)
dune_raster = rasterio.open(dune_input)
sand_raster = rasterio.open(sand_input)
sachi_raster = rasterio.open(sachi_input)
nssi_raster = rasterio.open(nssi_input)
ecotype_raster = rasterio.open(ecotype_input)
gmt2_raster = rasterio.open(gmt2_input)
water_raster = rasterio.open(water_input)

# Prepare output profile
output_profile = wetland_raster.profile.copy()
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

# Compile surficial features
print(f'Compiling surficial features...')
iteration_start = time.time()
with rasterio.open(surficial_output, 'w', **output_profile) as dst:
    # Find number of raster blocks
    window_list = []
    for block_index, window in area_raster.block_windows(1):
        window_list.append(window)
    # Iterate processing through raster blocks
    count = 1
    progress = 0
    for block_index, window in area_raster.block_windows(1):
        #### LOAD BLOCKS
        area_block = area_raster.read(window=window, masked=False)
        wetland_block = wetland_raster.read(window=window, masked=False)
        esa_block = esa_raster.read(window=window, masked=False)
        esri_block = esri_raster.read(window=window, masked=False)
        landfire_block = landfire_raster.read(window=window, masked=False)
        geomorph_block = geomorph_raster.read(window=window, masked=False)
        barren_block = barren_raster.read(window=window, masked=False)
        coastal_block = coastal_raster.read(window=window, masked=False)
        dune_block = dune_raster.read(window=window, masked=False)
        sand_block = sand_raster.read(window=window, masked=False)
        sachi_block = sachi_raster.read(window=window, masked=False)
        nssi_block = nssi_raster.read(window=window, masked=False)
        ecotype_block = ecotype_raster.read(window=window, masked=False)
        gmt2_block = gmt2_raster.read(window=window, masked=False)
        water_block = water_raster.read(window=window, masked=False)

        #### BEGIN PROGRAMMATIC KEY

        # Set base value
        out_block = np.where(area_block == 1, 0, nodata_value)

        #### 0. Compile physical features

        # 0.1 Barren
        out_block = np.where(((barren_block == 1) & (esri_block == 8))
                             | ((barren_block == 1) & (esa_block == 60))
                             | ((esri_block == 8) & (esa_block == 60)),
                             1, out_block)

        # 0.2 Coastal Barren
        out_block = np.where((out_block == 1) & (coastal_block == 1),
                              2, out_block)

        # 0.3 Coastal saline
        out_block = np.where((out_block == 0) & (coastal_block == 1),
                             3, out_block)

        # 0.4 Coastal Dunes
        out_block = np.where(((out_block == 2) | (out_block == 3)) & (dune_block == 1),
                             4, out_block)

        # 0.5 Inland Dunes
        out_block = np.where(((out_block == 0) | (out_block == 1)) & (sand_block == 1) & (dune_block == 1),
                             5, out_block)

        # 0.8 Freshwater Waterbody
        out_block = np.where((((wetland_block == 5) & (esa_block == 80))
                              | ((wetland_block == 5) & ((esri_block == 1) | (esri_block == 0)))
                              | ((esa_block == 80) & ((esri_block == 1) | (esri_block == 0))))
                             & (coastal_block == 0),
                             8, out_block)

        # 0.9 Marine Waterbody
        out_block = np.where((((wetland_block == 5) & (esa_block == 80))
                              | ((wetland_block == 5) & ((esri_block == 1) | (esri_block == 0)))
                              | ((esa_block == 80) & ((esri_block == 1) | (esri_block == 0)))
                              | (water_block == 1))
                             & (coastal_block == 1),
                             9, out_block)

        # 0.7 Infrastructure from NSSI
        out_block = np.where((nssi_block == 1) | (nssi_block == 2) | (nssi_block == 3),
                             7, out_block)

        # 0.7 Infrastructure from SACHI
        out_block = np.where((out_block == 0) & ((sachi_block == 11) | (sachi_block == 12)
                                                 | (sachi_block == 13) | (sachi_block == 20)
                                                 | (sachi_block == 30) | (sachi_block == 40)),
                             7, out_block)

        # 0.7 Infrastructure from ESA World Cover
        out_block = np.where((out_block == 0) & (esa_block == 50),
                             7, out_block)

        # Set no data values from area raster to no data
        out_block = np.where(area_block == 1, out_block, nodata_value)

        # Write results
        dst.write(out_block,
                  window=window)
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
with rasterio.open(surficial_output, 'r+') as dst:
    # Build pyramids with bilinear resampling
    dst.build_overviews(overview_levels, resampling=Resampling.mode)
    # Update metadata to indicate overviews exist
    dst.update_tags(ns='rio_overview', resampling='mode')
end_timing(iteration_start)

#### BUILD RASTER ATTRIBUTE TABLE
####____________________________________________________

# Create dictionary of value labels
value_labels = {
    0: 'Unassigned',
    1: 'Barren',
    2: 'Coastal Barren',
    3: 'Coastal Saline',
    4: 'Coastal Dune',
    5: 'Inland Dune',
    6: 'Patterned Ground',
    7: 'Infrastructure',
    8: 'Freshwater',
    9: 'Marine Water'
}

# Specify attribute table file path
attribute_output = surficial_output + '.vat.dbf'
if os.path.exists(attribute_output):
    os.remove(attribute_output)

# Define new collection counter
value_counts = collections.Counter()

# Read raster blocks to build attribute values and counts
print('Building value histogram...')
iteration_start = time.time()
with rasterio.open(surficial_output) as surficial_raster:
    # Find number of raster blocks
    window_list = []
    for block_index, window in surficial_raster.block_windows(1):
        window_list.append(window)
    # Iterate processing through raster blocks
    count = 1
    progress = 0
    for block_index, window in surficial_raster.block_windows(1):
        input_block = surficial_raster.read(1, window=window, masked=True)
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
    0: 'E1E1E1',
    1: 'FFFFBE',
    2: 'E69800',
    3: '9EAAD7',
    4: 'F5CA7A',
    5: '897044',
    6: '006400',
    7: 'FA0000',
    8: 'BEE8FF',
    9: 'BED2FF'
}

# Specify colormap file path
colormap_output = surficial_output + '.clr'
if os.path.exists(colormap_output):
    os.remove(colormap_output)

# Write colormap
print('Writing colormap...')
with open(colormap_output, 'w') as f:
    for value, hex_color in value_colors.items():
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        f.write(f'{value} {r} {g} {b}\n')
    f.write('END\n')
