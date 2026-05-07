# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Monitoring site selection for Icy Cape
# Author: Timm Nawrocki
# Last Updated: 2026-04-23
# Usage: Execute in Python 3.9+.
# Description: 'Monitoring site selection for Icy Cape' selects long-term monitoring sites based on random points distributed within strata, which correspond to map classes in the 1:10,000 scale map.
# ---------------------------------------------------------------------------

# Define region
region = 'IcyCape'

# Define selection parameters
total_sites = 18
min_distance_stratum = 120
min_distance_all = 60
omitted_values = [174, 176, 177] # Omit sampling from infrastructure and water
seed = 1

# Import packages
import os
import random
import numpy as np
from scipy import ndimage
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
installation_input = os.path.join(input_folder, f'region_data/{region}_Installation_3338.shp')
evt_input = os.path.join(output_folder, f'vegetation_data/{region}_Vegetation_{year}_900mmu_2m_3338.tif')
label_input = os.path.join(repository_folder, 'value_labels.json')
sample_input = os.path.join(repository_folder, 'value_samples.json')

# Define output files
strata_output = os.path.join(output_folder, f'monitoring_sites/{region}_Strata_v1p0_3338.shp')
site_output = os.path.join(output_folder, f'monitoring_sites/{region}_Sites_v1p0_3338.shp')

#### CONVERT VEGETATION RASTER TO POLYGON
####____________________________________________________

# Load the installation boundary and extract the geometry for masking
installation_data = gpd.read_file(installation_input)
installation_data['geometry'] = installation_data.geometry.buffer(-15)
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

    print('Expanding omitted raster classes by 10 m...')
    # Create a boolean mask where True represents an omitted value
    exclusion_zone = np.isin(veg_data, omitted_values)

    # Expand (dilate) True values outward by 5 pixels (pixels are 2 m)
    exclusion_zone = ndimage.binary_dilation(exclusion_zone, iterations=5)

    # Overwrite the original raster with the new exclusion zone
    veg_data[exclusion_zone] = nodata_value

    # Create a mask to remove nodata
    valid_mask = (veg_data != nodata_value)

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

# Load the JSON sample number data
with open(sample_input, 'r') as f:
    raw_samples = json.load(f)
value_samples = {
    int(k): int(v)
    for k, v in raw_samples.items() if int(k) in unique_values
}

# Clip and dissolve records by stratum (i.e., create multipolygons)
print('Clipping and dissolving geometries by stratum...')
strata_data = gpd.GeoDataFrame(records, crs=crs)
strata_data = gpd.clip(strata_data, installation_data)
strata_data = strata_data.dissolve(by='stratum').reset_index()

#### FILTER STRATA BY AREA PERCENTAGE
####____________________________________________________

# Calculate the total area of the installation
print('Filtering strata by area percentage (0.5% threshold)...')
installation_area = installation_data.geometry.area.sum()

# Calculate the area of each stratum
strata_data['area_m2'] = strata_data.geometry.area
strata_data['area_pct'] = (strata_data['area_m2'] / installation_area) * 100

# Omit strata that occupy less than 0.5% of the installation
strata_data = strata_data[strata_data['area_pct'] >= 0.5].copy()
print(f'Sites will be drawn from {len(strata_data)} strata...')

#### APPLY INTERNAL BUFFER
####____________________________________________________

print('Applying internal negative buffer...')

# Split dissolved geometries into individual polygons
strata_data = strata_data.explode(index_parts=False)

# Define a function to iteratively apply a buffer depending on polygon size
def iterative_buffer(geometry, buffer_distance=-15, min_area=16):
    # Calculate buffered geometry using original buffer distance
    buffered_geometry = geometry.buffer(buffer_distance)
    # Check if the buffered geometry is smaller than the limit
    if buffered_geometry.is_empty or buffered_geometry.area < min_area:
        # Calculate buffered geometry using reduced buffer distance
        buffered_geometry = geometry.buffer(buffer_distance + 10)
    # Return the variable buffered geometry
    return buffered_geometry

# iteratively apply a buffer to each individual geometry
strata_data['geometry'] = strata_data.geometry.apply(
    lambda x: iterative_buffer(x)
)

# Eliminate empty or invalid geometries
strata_data = strata_data[~strata_data.geometry.is_empty & strata_data.geometry.is_valid]

# Dissolve records by stratum (i.e., create multipolygons)
strata_data = strata_data.dissolve(by='stratum').reset_index()

# Export strata geometries
strata_data.to_file(strata_output)

#### SELECT MONITORING SITES
####____________________________________________________

print('Executing random stratified point generation...')

# Set random seed
random.seed(seed)

# Create dictionaries to track geometries and points
strata_geoms = {row['stratum']: row['geometry'] for _, row in strata_data.iterrows()}
selected_sites = {stratum: [] for stratum in strata_geoms.keys()}
all_points_global = []

# Implement selection counter
sites_n = 0

# Perform iterative site selection
while sites_n < total_sites:

    # Shuffle the strata keys
    stratum_keys = list(strata_geoms.keys())
    random.shuffle(stratum_keys)

    # Points added during the current iteration
    iteration_point_n = 0

    # Select sites
    for stratum in stratum_keys:

        # Break immediately if the total target is reached midway through a round
        if sites_n >= total_sites:
            break

        # Identify the target number of sites for the stratum
        stratum_n = value_samples.get(stratum, 0)

        # Filter geometries to the stratum
        stratum_geometry = strata_geoms[stratum]
        existing_sites = selected_sites[stratum]
        bounds = stratum_geometry.bounds

        # Initialize search parameters
        point_found = False
        attempts = 0
        max_attempts = 10000

        # Search for a new point for the stratum if the stratum limit has not been reached
        if len(existing_sites) < stratum_n:
            while not point_found and attempts < max_attempts:
                # Generate a random X/Y coordinate within the bounding box of the stratum
                x = random.uniform(bounds[0], bounds[2])
                y = random.uniform(bounds[1], bounds[3])
                candidate_point = Point(x, y)

                # Check if the point falls inside the stratum geometry
                if stratum_geometry.contains(candidate_point):
                    # Create logic checks for point neighbor distance thresholds
                    check_stratum = all(candidate_point.distance(p) >= min_distance_stratum for p in existing_sites)
                    check_global = all(candidate_point.distance(p) >= min_distance_all for p in all_points_global)

                    # Check if the point is too close to existing neighbors
                    if check_stratum and check_global:
                        selected_sites[stratum].append(candidate_point)
                        all_points_global.append(candidate_point)
                        sites_n += 1
                        iteration_point_n += 1
                        point_found = True

                # Increase the counter for attempts
                attempts += 1

    # Break the loop if no additional points can be added because of spacing rules
    if iteration_point_n == 0:
        print(f'Selection stopped early at {sites_n} sites. Stratum max capacities or spatial limits reached.')
        break

#### PREPARE DATA FOR EXPORT
####____________________________________________________

# Format the output records
print('Formatting and exporting shapefile...')
output_records = []
for stratum, points in selected_sites.items():
    for point in points:
        # Fetch the text label for the output attribute table
        stratum_label = value_labels.get(stratum, 'Unknown')
        # Build the geometry attributes
        output_records.append({
            'value': stratum,
            'stratum': stratum_label,
            'modified': 'false',
            'geometry': point
        })

# Shuffle the records list so that site_code assignment is random
random.shuffle(output_records)

# Iterate through shuffled records to assign the site_code
for i, record in enumerate(output_records, start=1):
    # Create a three-digit string with leading zeros
    record['site_code'] = f'{prefix}-{i:03d}'

# Build final GeoDataFrame
site_data = gpd.GeoDataFrame(output_records, crs=crs)

# Reorder columns so site_code is the primary attribute in the table
column_order = ['site_code', 'value', 'stratum', 'modified', 'geometry']
site_data = site_data[column_order]

#### PERFORM MANUAL ADJUSTMENTS AND EXPORT DATA
####____________________________________________________

print('Applying manual site overrides...')

# Apply manual updates to NVIC-013
if 'NVIC-013' in site_data['site_code'].values:
    row_idx_013 = site_data['site_code'] == 'NVIC-013'
    site_data.loc[row_idx_013, 'geometry'] = Point(-302649.31, 2274641.63)
    site_data.loc[row_idx_013, 'value'] = 140
    site_data.loc[row_idx_013, 'stratum'] = value_labels.get(140, 'Unknown')
    site_data.loc[row_idx_013, 'modified'] = 'true'
else:
    print('Notice: NVIC-013 not found. Override skipped.')

# Apply manual updates to NVIC-002
if 'NVIC-002' in site_data['site_code'].values:
    row_idx_002 = site_data['site_code'] == 'NVIC-002'
    site_data.loc[row_idx_002, 'geometry'] = Point(-302934.84, 2274116.05)
    site_data.loc[row_idx_002, 'value'] = 180
    site_data.loc[row_idx_002, 'stratum'] = value_labels.get(180, 'Unknown')
    site_data.loc[row_idx_002, 'modified'] = 'true'
else:
    print('Notice: NVIC-002 not found. Override skipped.')

# Export to Shapefile
site_data.to_file(site_output)
print(f'Successfully generated {sites_n} monitoring sites.')
