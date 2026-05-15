# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Parse AKVEG Map metadata from template
# Author: Timm Nawrocki
# Last Updated: 2026-05-14
# Usage: Execute in Python 3.9+.
# Description: 'Parse AKVEG Map metadata from template' replaces metadata specific to each map unit and raster extent.
# ---------------------------------------------------------------------------

# Define regions
region = 'Utqiagvik'

# Import packages
import os
import rasterio
from pyproj import Transformer

# Define dictionary for installation years
region_years = {
    'IcyCape': '20200714',
    'Utqiagvik': '20240710',
    'McIntyre': '20220803'
}

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
input_folder = os.path.join(project_folder, 'Data_Output/data_package/20260514_arctic_navy')

# Define input files
date_string = region_years.get(region)
raster_input = os.path.join(input_folder, f'reference_images/{region}_Imagery_{date_string}_0.5m_3338.tif')

# Setup pyproj transformer for EPSG:3338 to EPSG:4326
transformer = Transformer.from_crs('EPSG:3338', 'EPSG:4326', always_xy=True)

#### DEFINE BOUNDS
####____________________________________________________


# Read raster bounds
try:
    with rasterio.open(raster_input) as src:
        bounds = src.bounds
except FileNotFoundError:(
    print(f'File not found, skipping: {raster_input}'))

# Convert raster bounds from EPSG:3338 to EPSG:4326
west_4326, south_4326 = transformer.transform(bounds.left, bounds.bottom)
east_4326, north_4326 = transformer.transform(bounds.right, bounds.top)

# Assign EPSG:4326 bounding coordinates rounded to 5 decimal places to variables
west_coordinate = round(west_4326, 5)
east_coordinate = round(east_4326, 5)
south_coordinate = round(south_4326, 5)
north_coordinate = round(north_4326, 5)
print(west_coordinate, east_coordinate, south_coordinate, north_coordinate)
