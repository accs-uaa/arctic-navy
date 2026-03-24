# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Create study area rasters
# Author: Timm Nawrocki
# Last Updated: 2026-03-23
# Usage: Must be executed in a Python 3.12+ installation.
# Description: 'Create study area rasters' converts a set of vector polygon study areas to rasters using imagery and segments to define the grid alignments at 0.5 and 2 m resolutions, respectively.
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

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
image_folder = os.path.join(project_folder, 'Data_Input/imagery_data')
segment_folder = os.path.join(project_folder, 'Data_Output/segment_data')
output_folder = os.path.join(project_folder, 'Data_Input/rasterized_data')
geodatabase = os.path.join(project_folder, 'DoD_Navy_Arctic.gdb')

# Define input files
icycape_input = os.path.join(image_folder, 'IcyCape_Imagery_20200714_0.5m_3338.tif')
utqiagvik_input = os.path.join(image_folder, 'Utqiagvik_Imagery_20240710_0.5m_3338.tif')
mcintyre_input = os.path.join(image_folder, 'Kuparuk_Imagery_20220803_0.5m_3338.tif')
icycape_2m_input = os.path.join(segment_folder, 'IcyCape_Segments_2m_3338.tif')
utqiagvik_2m_input = os.path.join(segment_folder, 'Utqiagvik_Segments_2m_3338.tif')
mcintyre_2m_input = os.path.join(segment_folder, 'McIntyre_Segments_2m_3338.tif')

# Define input features
feature_list = ['IcyCape_StudyArea_3338', 'Utqiagvik_StudyArea_3338', 'McIntyre_StudyArea_3338',
             'IcyCape_StudyArea_3338', 'Utqiagvik_StudyArea_3338', 'McIntyre_StudyArea_3338']
grid_list = [icycape_input, utqiagvik_input, mcintyre_input,
             icycape_2m_input, utqiagvik_2m_input, mcintyre_2m_input]

#### RASTERIZE FEATURES
####____________________________________________________

# Convert each feature and convert to raster
count = 1
for feature in feature_list:

    # Define resolution
    if count <= 3:
        resolution = '0.5m'
    else:
        resolution = '2m'

    # Define output name
    file_name = feature.replace('_3338', f'_{resolution}_3338.tif')
    raster_output = os.path.join(output_folder, file_name)

    # Convert feature to raster if it does not already exist
    if not os.path.exists(raster_output):
        start_time = time.time()
        print(f'Rasterizing {feature}...')

        # Define snap raster and study area
        grid_input = grid_list[count-1]
        study_area = gpd.read_file(geodatabase, layer=feature)
        print(grid_input)

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
        shape_data = ((geom, 1) for geom in study_area.geometry)

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

    count += 1
