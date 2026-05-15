# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Parse AKVEG Map metadata from template
# Author: Timm Nawrocki
# Last Updated: 2026-05-14
# Usage: Execute in Python 3.9+.
# Description: 'Parse AKVEG Map metadata from template' replaces metadata specific to each map unit and raster extent.
# ---------------------------------------------------------------------------

# Import packages
import os
import rasterio
from pyproj import Transformer

# Define regions
regions = {'IcyCape': 'Icy Cape',
           'Utqiagvik': 'Point Barrow',
           'McIntyre': 'Point McIntyre'}

# Define diagnostic sets
diagnostic_sets = {'betshr': 'birch shrubs',
                   'dryas': 'Dryas dwarf shrubs',
                   'dsalix': 'willow dwarf shrubs',
                   'erivag': 'tussock cottongrass',
                   'feather': 'feathermoss',
                   'halgra': 'halophytic graminoids',
                   'lichen': 'lichens',
                   'ndsalix': 'willow shrubs',
                   'nerishr': 'needleleaf ericaceous shrubs',
                   'sphagn': 'Sphagnum mosses',
                   'terrestrialwater': 'terrestrial water',
                   'wetforb': 'wetland forbs',
                   'wetsed': 'wetland sedges'}

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
input_folder = os.path.join(project_folder, 'Data_Output/data_package/20260514_arctic_navy/akveg_data')
output_folder = os.path.join(project_folder, 'Data_Output')

# Define input files
foliar_template = os.path.join(output_folder, 'metadata/templates/AKVEG_FoliarCover_10m_3338.xml')
water_template = os.path.join(output_folder, 'metadata/templates/AKVEG_TerrestrialWater_10m_3338.xml')

# Setup pyproj transformer for EPSG:3338 to EPSG:4326
transformer = Transformer.from_crs('EPSG:3338', 'EPSG:4326', always_xy=True)

#### PARSE METADATA FROM TEMPLATE
####____________________________________________________

# Loop through regions and diagnostic sets
for region_short, region_full in regions.items():
    for map_set, unit_name in diagnostic_sets.items():
        # Define input raster dataset
        raster_input = os.path.join(input_folder, f'{region_short}_{map_set}_10m_3338.tif')

        # Define output metadata file
        metadata_output = os.path.join(output_folder, f'metadata/{region_short}_{map_set}_10m_3338.xml')

        # Read raster bounds
        try:
            with rasterio.open(raster_input) as src:
                bounds = src.bounds
        except FileNotFoundError:
            print(f'File not found, skipping: {raster_input}')
            continue

        # Convert raster bounds from EPSG:3338 to EPSG:4326
        west_4326, south_4326 = transformer.transform(bounds.left, bounds.bottom)
        east_4326, north_4326 = transformer.transform(bounds.right, bounds.top)

        # Assign EPSG:4326 bounding coordinates rounded to 5 decimal places to variables
        west_coordinate = round(west_4326, 5)
        east_coordinate = round(east_4326, 5)
        south_coordinate = round(south_4326, 5)
        north_coordinate = round(north_4326, 5)

        # Read metadata from template
        if map_set == 'terrestrialwater':
            with open(water_template, 'r', encoding='utf-8') as file:
                metadata_content = file.read()
        else:
            with open(foliar_template, 'r', encoding='utf-8') as file:
                metadata_content = file.read()

        # Replace 'Icy Cape' with the region_full variable text string
        metadata_content = metadata_content.replace('Icy Cape', region_full)

        # Replace 'Birch Shrubs' with unit_name.title()
        metadata_content = metadata_content.replace('Birch Shrubs', unit_name.title())

        # Replace 'birch shrubs' with unit_name
        metadata_content = metadata_content.replace('birch shrubs', unit_name)

        # Replace <gco:Decimal>172.44459</gco:Decimal> with <gco:Decimal>{west_coordinate}</gco:Decimal>
        metadata_content = metadata_content.replace('<gco:Decimal>172.44459</gco:Decimal>',
                                                    f'<gco:Decimal>{west_coordinate}</gco:Decimal>')

        # Replace <gco:Decimal>-129.99545</gco:Decimal> with <gco:Decimal>{east_coordinate}</gco:Decimal>
        metadata_content = metadata_content.replace('<gco:Decimal>-129.99545</gco:Decimal>',
                                                    f'<gco:Decimal>{east_coordinate}</gco:Decimal>')

        # Replace <gco:Decimal>51.21576</gco:Decimal> with <gco:Decimal>{south_coordinate}</gco:Decimal>
        metadata_content = metadata_content.replace('<gco:Decimal>51.21576</gco:Decimal>',
                                                    f'<gco:Decimal>{south_coordinate}</gco:Decimal>')

        # Replace <gco:Decimal>71.38949</gco:Decimal> with <gco:Decimal>{north_coordinate}</gco:Decimal>
        metadata_content = metadata_content.replace('<gco:Decimal>71.38949</gco:Decimal>',
                                                    f'<gco:Decimal>{north_coordinate}</gco:Decimal>')

        # Export metadata file
        with open(metadata_output, 'w', encoding='utf-8') as file:
            file.write(metadata_content)

        print(f'Successfully processed {region_full} {unit_name}...')
