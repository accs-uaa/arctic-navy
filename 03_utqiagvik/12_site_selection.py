# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Monitoring site selection for Icy Cape
# Author: Timm Nawrocki
# Last Updated: 2026-04-23
# Usage: Execute in Python 3.9+.
# Description: 'Monitoring site selection for Icy Cape' selects long-term monitoring sites based on random points distributed within strata, which correspond to map classes in the 1:10,000 scale map.
# ---------------------------------------------------------------------------

# Define region
region = 'Utqiagvik'

# Define selection parameters
total_sites = 18
sites_per_stratum = 6
min_distance_m = 150
buffer_distance = -15

# Import packages
import os
import random
import numpy as np
import geopandas as gpd
import json
import rasterio
from rasterio.mask import mask
from rasterio.features import shapes
from shapely.geometry import shape, Point

# Define nodata value
nodata_value = 255

# Define year and prefix variable
if region == 'IcyCape':
    year = 2020
    prefix = 'NVIC'
elif region == 'McIntyre':
    year = 2022
    prefix = 'NVMC'
elif region == 'Utqiagvik':
    year = 2024
    prefix = 'NVBR'
else:
    quit()

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
repository_folder = os.path.join(drive, root_folder, 'Repositories/arctic-navy')
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
input_folder = os.path.join(project_folder, 'Data_Input')
output_folder = os.path.join(project_folder, 'Data_Output')

# Define input files
installation_input = os.path.join(input_folder, f'region_data/Barrow_Installation_Main_3338.shp')
evt_input = os.path.join(output_folder, f'vegetation_data/{region}_Vegetation_{year}_900mmu_2m_3338.tif')
label_input = os.path.join(repository_folder, 'value_labels.json')

# Define output files
site_output = os.path.join(output_folder, f'monitoring_sites/{region}_Sites_v1p0_3338.shp')

#### CONVERT VEGETATION RASTER TO POLYGON
####____________________________________________________

# Load the installation boundary and extract the geometry for masking
installation_data = gpd.read_file(installation_input)
installation_data['geometry'] = installation_data.geometry.buffer(-5)
installation_geoms = [geom for geom in installation_data.geometry]

# Convert raster geometries to vector records
print('Cropping raster to installation boundary and converting to polygons...')
with rasterio.open(evt_input) as veg_raster:
    # Define crs
    crs = veg_raster.crs

    # Read raster data within the installation boundary
    veg_data, out_transform = mask(
        veg_raster,
        installation_geoms,
        crop=True,
        nodata=nodata_value
    )

    # Retrieve the 2d band array from the raster data
    veg_data = veg_data[0]

    # Create a mask to remove nodata, infrastructure, and water (terrestrial and marine)
    omitted_values = [174, 176, 177]
    valid_mask = (veg_data != nodata_value) & (~np.isin(veg_data, omitted_values))

    # Extract unique values present in the valid data area
    unique_values = np.unique(veg_data[valid_mask])

    # Generate vector shapes from the masked raster pixels
    geometries = shapes(veg_data, mask=valid_mask, transform=out_transform)

    # Format into records for GeoPandas
    records = [
        {'stratum': value, 'geometry': shape(geometry)}
        for geometry, value in geometries
    ]

# Load the JSON label data
with open(label_input, 'r') as f:
    raw_labels = json.load(f)
value_labels = {
    int(k): v
    for k, v in raw_labels.items() if int(k) in unique_values
}

# Clip and dissolve records by stratum (i.e., create multipolygons)
print('Clipping and dissolving geometries by stratum...')
strata_data = gpd.GeoDataFrame(records, crs=crs)
strata_data = gpd.clip(strata_data, installation_data)
strata_data = strata_data.dissolve(by='stratum').reset_index()

#### FILTER STRATA BY AREA PERCENTAGE
####____________________________________________________

# Calculate the total area of the installation
print('Filtering strata by area percentage (0.1% threshold)...')
installation_area = installation_data.geometry.area.sum()

# Calculate the area of each stratum
strata_data['total_area_m2'] = strata_data.geometry.area
strata_data['area_pct'] = (strata_data['total_area_m2'] / installation_area) * 100

# Omit strata that occupy less than 0.1% of the installation
strata_data = strata_data[strata_data['area_pct'] >= 0.1].copy()
print(f'Sites will be drawn from {len(strata_data)} strata...')

#### APPLY INTERNAL BUFFER
####____________________________________________________

# Apply negative inward buffer
print('Applying internal negative buffer to eliminate edge overlap...')
strata_data['geometry'] = strata_data.geometry.buffer(buffer_distance)

# Drop any strata/polygons that disappeared completely due to being too narrow
strata_data = strata_data[~strata_data.geometry.is_empty & strata_data.geometry.is_valid]

#### SELECT MONITORING SITES
####____________________________________________________

print('Executing random stratified point generation...')

# Set random seed
random.seed(2)

# Create dictionaries to track geometries and points
strata_geoms = {row['stratum']: row['geometry'] for _, row in strata_data.iterrows()}
selected_sites = {stratum: [] for stratum in strata_geoms.keys()}
all_points_global = []

# Implement selection counter
sites_n = 0

# Perform up to 4 iterations of site selection
for round_num in range(sites_per_stratum):

    # Shuffle the strata keys
    stratum_keys = list(strata_geoms.keys())
    random.shuffle(stratum_keys)

    # Select sites
    for stratum in stratum_keys:
        # Break the loop if the installation-wide limit is hit
        if sites_n >= total_sites:
            break

        # Filter geometries to stratum
        stratum_geometry = strata_geoms[stratum]
        existing_sites = selected_sites[stratum]
        bounds = stratum_geometry.bounds

        # Initialize search parameters
        point_found = False
        attempts = 0
        max_attempts = 10000

        # Search for a new point for the stratum
        while not point_found and attempts < max_attempts:
            # Generate a random X/Y coordinate within the bounding box of the stratum
            x = random.uniform(bounds[0], bounds[2])
            y = random.uniform(bounds[1], bounds[3])
            candidate_point = Point(x, y)

            # Check if the point falls inside the stratum geometry
            if stratum_geometry.contains(candidate_point):
                # Create logic checks for point neighbor distance thresholds
                check_stratum = all(candidate_point.distance(p) >= min_distance_m for p in existing_sites)
                check_global = all(candidate_point.distance(p) >= 80 for p in all_points_global)

                # Check if the point is too close to existing neighbors
                if check_stratum and check_global:
                    selected_sites[stratum].append(candidate_point)
                    all_points_global.append(candidate_point)
                    sites_n += 1
                    point_found = True

            attempts += 1

#### EXPORT DATA
####____________________________________________________

# Format the output records
print('Formatting and exporting shapefile...')
output_records = []
for stratum, points in selected_sites.items():
    for point in points:
        # Fetch the text label for the output attribute table
        stratum_label = value_labels.get(stratum, 'Unknown')
        output_records.append({
            'value': stratum,
            'stratum': stratum_label,
            'geometry': point
        })

# Process output records if they were successfully generated (i.e., dataframe is not empty)
if output_records:
    # Shuffle the records list so that site_code assignment is random
    random.shuffle(output_records)

    # Iterate through shuffled records to assign the site_code
    for i, record in enumerate(output_records, start=1):
        # Create a three-digit string with leading zeros
        record['site_code'] = f'{prefix}-{i:03d}'

    # Build final GeoDataFrame
    sites_data = gpd.GeoDataFrame(output_records, crs=crs)

    # Reorder columns so site_code is the primary attribute in the table
    column_order = ['site_code', 'value', 'stratum', 'geometry']
    sites_data = sites_data[column_order]

    # Export to Shapefile
    sites_data.to_file(site_output)
    print(f'Successfully generated {sites_n} monitoring sites with randomized codes.')

# Avoid output for empty records
else:
    print('Warning: No sites could be generated. Strata geometries may be too small after buffering.')
