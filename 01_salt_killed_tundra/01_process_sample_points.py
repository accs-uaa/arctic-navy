# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Process sample points for salt-killed tundra
# Author: Timm Nawrocki
# Last Updated: 2026-03-05
# Usage: Must be executed in a Python 3.12+ installation.
# Description: 'Process sample points for salt-killed tundra' creates a random sample of points where the GMT-2 results indicated salt-killed tundra.
# ---------------------------------------------------------------------------

# Import packages
import ee
import os
import time
import numpy as np
import pandas as pd
import rasterio
from google.cloud import storage
from akutils import *

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
ancillary_folder = os.path.join(project_folder,
                                'Data_Input/ancillary_data/GMT2_SurficialFeatures_2m/unprocessed')
output_folder = os.path.join(project_folder, 'Data_Input/surficial_data')

# Define input files
gmt2_input = os.path.join(ancillary_folder, 'GMT2_SurficialFeatures.tif')

# Define output files
salt_output = os.path.join(output_folder, 'NorthSlope_SaltKilled_3338.csv')

# Define paths
ee_project = 'akveg-map'
storage_bucket = 'akveg-data'
export_prefix = 'arctic_navy'
file_name = os.path.basename(salt_output)
storage_path = f'arctic_navy/surficial_data/{file_name}'
asset_path = f'projects/{ee_project}/assets'

# Define asset
gcs_uri = f'gs://{storage_bucket}/{storage_path}'
asset_id = f'{asset_path}/{export_prefix}/NorthSlope_SaltKilled'

#### PROCESS RASTER EXTRACTION
####____________________________________________________
print('Sampling points from raster...')
start_time = time.time()

# Define parameters
target_value = 13
num_samples = 5000
min_distance_m = 20

# Define a function to sample and extract coordinates
def sample_pixels(rows, cols, raster_data, transform, n_samples):
    # Identify number of rows
    n_available = len(rows)

    # Return empty data frame if there are no rows
    if n_available == 0:
        print(f'Warning: No pixels found.')
        return pd.DataFrame()

    # Oversample the raster
    oversample_size = min(n_samples * 10, n_available)
    oversample_index = np.random.choice(n_available, size=oversample_size, replace=False)
    oversample_rows = rows[oversample_index]
    oversample_cols = cols[oversample_index]

    # Convert sample indices to coordinates
    cent_x, cent_y = rasterio.transform.xy(transform, oversample_rows, oversample_cols, offset='center')

    # Iteratively filter points by minimum distance
    selected_indices = []
    selected_coords = []
    for i in range(len(cent_x)):
        if len(selected_indices) >= n_samples:
            break

        # Define sample set
        current_coord = np.array([cent_x[i], cent_y[i]])

        # Sample points based on distances
        if len(selected_coords) == 0:
            # Always accept the first point
            selected_coords.append(current_coord)
            selected_indices.append(oversample_index[i])
        else:
            # Calculate squared distance to all currently accepted points
            diffs = np.array(selected_coords) - current_coord
            dist_sq = np.sum(diffs ** 2, axis=1)

            # Check if all existing points are further than the minimum distance
            if np.all(dist_sq >= (min_distance_m ** 2)):
                selected_coords.append(current_coord)
                selected_indices.append(oversample_index[i])

    if len(selected_indices) < n_samples:
        print(f'Warning: Only {len(selected_indices)} points satisfying the {min_distance_m} m minimum distance.')

    # Extract final values based on the surviving indices
    final_rows = rows[selected_indices]
    final_cols = cols[selected_indices]
    sampled_values = raster_data[final_rows, final_cols]
    cent_x, cent_y = rasterio.transform.xy(transform, final_rows, final_cols, offset='center')

    return pd.DataFrame({
        'cent_x': cent_x,
        'cent_y': cent_y,
        'saltkilled': sampled_values
    })

# Read raster metadata
with rasterio.open(gmt2_input) as gmt2_raster:
    raster_data = gmt2_raster.read(1)
    raster_meta = gmt2_raster.meta
    raster_transform = gmt2_raster.transform
    nodata_value = gmt2_raster.nodata

# Sample target value
target_rows, target_cols = np.where((raster_data == target_value) & (raster_data != nodata_value))
target_data = sample_pixels(target_rows, target_cols, raster_data, raster_transform, num_samples)

# Sample non-target values
nontarget_rows, nontarget_cols = np.where((raster_data != target_value) & (raster_data != nodata_value))
nontarget_data = sample_pixels(nontarget_rows, nontarget_cols, raster_data, raster_transform, num_samples)

# Concatenate the samples
sample_data = pd.concat([target_data, nontarget_data], ignore_index=True)

# Reset raster values
sample_data['saltkilled'] = np.where(sample_data['saltkilled'] == 13, 1, 0)

# Export sample data to csv
sample_data.to_csv(salt_output, index=False)
end_timing(start_time)

#### STAGE TABLE ON GOOGLE CLOUD
####____________________________________________________
print('Uploading CSV to Google Cloud Storage...')

# Attempt to upload the csv to Google Cloud Storage
try:
    # Initialize the Google Cloud Storage client
    storage_client = storage.Client()
    start_time = time.time()

    # Locate the bucket and define the destination blob (file path)
    bucket = storage_client.bucket(storage_bucket)
    blob = bucket.blob(storage_path)

    # Upload the local file
    blob.upload_from_filename(salt_output)
    end_timing(start_time)

except Exception as e:
    print(f'Error during Google Cloud Storage upload: {e}')
    print('Please ensure your environment is authenticated with Google Cloud.')

#### INGEST TABLE TO EARTH ENGINE
####____________________________________________________

# Authenticate Earth Engine
print('Connecting to Earth Engine server...')
try:
    ee.Initialize(project=ee_project)
except Exception as e:
    print('Prompting authentication...')
    ee.Authenticate()
    ee.Initialize(project=ee_project)

# Construct the ingestion manifest
manifest = {
    'name': asset_id,
    'sources': [
        {
            'uris': [gcs_uri],
            'xColumn': 'cent_x',
            'yColumn': 'cent_y',
            'crs': 'EPSG:3338'
        }
    ]
}

# Generate a unique task ID and submit the ingestion request
task_id = ee.data.newTaskId()[0]
ee.data.startTableIngestion(task_id, manifest)
print('Initiated ingestion task.')
