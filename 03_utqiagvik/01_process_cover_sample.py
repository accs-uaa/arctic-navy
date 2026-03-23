# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Process cover sample
# Author: Timm Nawrocki
# Last Updated: 2026-03-20
# Usage: Must be executed in a Python 3.12+ installation.
# Description: 'Process cover sample' creates a random sample of cover values from the foliar cover rasters to serve as training data for transfer models.
# ---------------------------------------------------------------------------

# Define region
region = 'Utqiagvik'

# Import packages
import ee
import os
import time
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from pyproj import Transformer
from google.cloud import storage
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
foliar_folder = os.path.join(project_folder, 'Data_Input/foliar_data/v2.1b')
output_folder = os.path.join(project_folder, 'Data_Input/training_data')

# Define input files
area_input = os.path.join(project_folder, 'Data_Input/ArcticCoastal_MapDomain_10m_3338.tif')
study_input = os.path.join(project_folder, f'Data_Input/region_data/{region}_TerrestrialArea_3338.shp')

# Define output files
transfer_output = os.path.join(output_folder, f'{region}_TransferSample_3338.csv')

# Define GCS paths
storage_bucket = 'arctic-navy'
file_name = os.path.basename(transfer_output)
storage_path = f'training_data/{file_name}'
gcs_uri = f'gs://{storage_bucket}/{storage_path}'

# Define GEE paths
ee_project = 'accs-geospatial-processing'
asset_prefix = 'arctic_navy'
asset_path = f'projects/{ee_project}/assets/{asset_prefix}'
asset_id = f'{asset_path}/training_data/{region}_TransferSample'

# Create input list for foliar cover maps
foliar_list = ['bromos', 'dryas', 'dsalix', 'erivag', 'halgra',
               'ndsalix', 'nerishr', 'sphagn', 'vacvit', 'watercor', 'wetsed']

#### PROCESS RASTER EXTRACTION
####____________________________________________________
print('Creating pixel subset for sampling...')
start_time = time.time()

# Read the input study areas
study_area = gpd.read_file(study_input)

# Parse coordinates for pixel centroids from area raster
with rasterio.open(area_input) as area_raster:
    # Mask to geometry and filter out nodata to get valid pixel locations
    area_image, area_transform = mask(area_raster, study_area.geometry, crop=True)
    area_image = area_image.squeeze()

    rows, cols = np.where(area_image != nodata_value)
    cent_x, cent_y = rasterio.transform.xy(area_transform, rows, cols, offset='center')

# Construct initial dataframe with coordinates
sample_points = pd.DataFrame({'cent_x': cent_x, 'cent_y': cent_y})

# Randomly sample rows
num_samples = 300000
if len(sample_points) > num_samples:
    sample_points = sample_points.sample(n=num_samples, random_state=314, replace=False).reset_index(drop=True)

# Convert to a GeoDataFrame (stored in native EPSG:3338)
sample_points = gpd.GeoDataFrame(
    sample_points,
    geometry=gpd.points_from_xy(sample_points.cent_x, sample_points.cent_y),
    crs='EPSG:3338'
)

# Create a list of (X, Y) coordinate tuples required by rasterio.sample
coords = [(x, y) for x, y in zip(sample_points.geometry.x, sample_points.geometry.y)]
end_timing(start_time)

# Sample values from all rasters and append values to the GeoDataFrame
for name in foliar_list:
    print(f'Extracting data for {name}...')
    start_time = time.time()

    # Define input raster
    foliar_input = os.path.join(foliar_folder, f'{region}_{name}_10m_3338.tif')

    # Extract raster values to points
    with rasterio.open(foliar_input) as foliar_raster:
        extracted_values = [val[0] for val in foliar_raster.sample(coords)]

    # Append the extracted values as a new column
    sample_points[name] = extracted_values
    end_timing(start_time)

# Clip the sample points to the study area
sample_points = gpd.clip(sample_points, study_area)

# Select export columns
export_columns = ['cent_x', 'cent_y'] + foliar_list
sample_points = sample_points[export_columns]

# Remove invalid data
sample_points = sample_points.dropna()
sample_points = sample_points[(sample_points[foliar_list] >= 0).all(axis=1)]

# Export to CSV
sample_points.to_csv(transfer_output, index=False)
print(f'Successfully exported {len(sample_points):,} points.')

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
    blob.upload_from_filename(transfer_output)
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
