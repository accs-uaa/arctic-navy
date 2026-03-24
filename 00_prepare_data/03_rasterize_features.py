# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Rasterize features
# Author: Timm Nawrocki
# Last Updated: 2026-03-21
# Usage: Must be executed in a Python 3.12+ installation.
# Description: 'Rasterize features' converts a set of vector polygon features to raster.
# ---------------------------------------------------------------------------

# Import packages
import os
import time
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from rasterio.windows import from_bounds
from akutils import *

# Set no data and pixel size
nodata_value = -127
pixel_size = 0.5

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
output_folder = os.path.join(project_folder, 'Data_Input/rasterized_data')
geodatabase = os.path.join(project_folder, 'DoD_Navy_Arctic.gdb')

# Define area features
icycape_input = os.path.join(output_folder, 'IcyCape_StudyArea_0.5m_3338.tif')
utqiagvik_input = os.path.join(output_folder, 'Utqiagvik_StudyArea_0.5m_3338.tif')
mcintyre_input = os.path.join(output_folder, 'McIntyre_StudyArea_0.5m_3338.tif')

# Define input features
area_list = ['IcyCape_StudyArea_3338', 'Utqiagvik_StudyArea_3338', 'McIntyre_StudyArea_3338']
feature_list = ['IcyCape_CoastalZone_3338', 'Utqiagvik_CoastalZone_3338', 'McIntyre_CoastalZone_3338',
                'IcyCape_Correction_Water_3338', 'IcyCape_Correction_SaltIntruded_3338',
                'IcyCape_Correction_Disturbed_3338', 'IcyCape_Correction_TidalMarsh_3338',
                'IcyCape_Correction_Coast_3338',
                'Utqiagvik_Correction_Water_3338', 'Utqiagvik_Correction_SaltIntruded_3338',
                'Utqiagvik_Correction_Willow_3338', 'Utqiagvik_Correction_Disturbed_3338',
                'McIntyre_Correction_Water_3338', 'McIntyre_Correction_SaltIntruded_3338',
                'McIntyre_Correction_Barren_3338', 'McIntyre_Dunes_3338', 'McIntyre_Floodplain_3338',
                'McIntyre_Correction_Disturbed_3338', 'McIntyre_Correction_Beach_3338',
                'IcyCape_Infrastructure_3338', 'Utqiagvik_Infrastructure_3338', 'McIntyre_Infrastructure_3338',
                'IcyCape_Installation_3338', 'Utqiagvik_Installation_3338', 'McIntyre_Installation_3338']

#### RASTERIZE FEATURES
####____________________________________________________

# Convert each feature and convert to raster
for feature in feature_list:
    # Define output name
    file_name = feature.replace('_3338', '_0.5m_3338.tif')
    raster_output = os.path.join(output_folder, file_name)

    # Convert feature to raster if it does not already exist
    if not os.path.exists(raster_output):
        start_time = time.time()
        print(f'Rasterizing {feature}...')

        # Define snap raster and study area
        if 'icycape' in feature.lower():
            grid_input = icycape_input
            study_area = gpd.read_file(geodatabase, layer=area_list[0])
        elif 'utqiagvik' in feature.lower():
            grid_input = utqiagvik_input
            study_area = gpd.read_file(geodatabase, layer=area_list[1])
        elif 'mcintyre' in feature.lower():
            grid_input = mcintyre_input
            study_area = gpd.read_file(geodatabase, layer=area_list[2])
        else:
            print('ERROR: Check input feature name.')
            quit()

        # Define bounds
        min_x, min_y, max_x, max_y = study_area.total_bounds

        # Align reference grid
        with rasterio.open(grid_input) as src:
            # Calculate the pixel window in the image that covers the vector bounds
            window = from_bounds(min_x, min_y, max_x, max_y, src.transform)

            # Snap the window to the nearest whole pixel grid
            window = window.round_lengths().round_offsets()

            # Extract the aligned dimensions and transform
            height = int(window.height)
            width = int(window.width)
            transform = src.window_transform(window)

        # Assign geometries a value of 1
        feature_data = gpd.read_file(geodatabase, layer=feature)
        shape_data = ((geom, 1) for geom in feature_data.geometry)

        # Rasterize the geometries using the snapped dimensions and transform
        raster_data = rasterize(
            shapes=shape_data,
            out_shape=(height, width),
            fill=nodata_value,
            transform=transform,
            all_touched=False,
            dtype=rasterio.int8
        )

        # Write to disk as an 8-bit signed GeoTIFF
        with rasterio.open(
                raster_output, 'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=rasterio.int8,
                crs=study_area.crs,
                transform=transform,
                nodata=nodata_value
        ) as out_raster:
            out_raster.write(raster_data, 1)

        end_timing(start_time)

    else:
        print(f'{file_name} already exists.')
