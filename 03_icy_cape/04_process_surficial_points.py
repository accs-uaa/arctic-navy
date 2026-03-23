# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Process surficial points
# Author: Timm Nawrocki
# Last Updated: 2026-03-20
# Usage: Must be executed in a Python 3.12+ installation.
# Description: 'Process surficial points' combines manually delineated training data into a single table and ingests the table as an Earth Engine asset.
# ---------------------------------------------------------------------------

# Define region
region = 'IcyCape'

# Import packages
import ee
import os
import time
import pandas as pd
import geopandas as gpd
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
output_folder = os.path.join(project_folder, 'Data_Input/training_data')
geodatabase = os.path.join(project_folder, 'DoD_Navy_Arctic.gdb')

# Define output data
surficial_output = os.path.join(output_folder, f'{region}_SurficialPoints_3338.csv')

# Define paths
ee_project = 'accs-geospatial-processing'
storage_bucket = 'arctic-navy'
export_prefix = 'arctic_navy'
file_name = os.path.basename(surficial_output)
storage_path = f'training_data/{file_name}'
asset_path = f'projects/{ee_project}/assets'

# Define asset
gcs_uri = f'gs://{storage_bucket}/{storage_path}'
asset_id = f'{asset_path}/{export_prefix}/training_data/{region}_SurficialPoints'

# Define input surficial features
surficial_features = ['water', 'mesic', 'wet', 'barren', 'tidal marsh', 'beach']
surficial_dictionary = {'water': 1,
                        'mesic': 2,
                        'wet': 3,
                        'barren': 4,
                        'tidal marsh': 5,
                        'beach': 6}

#### MERGE TRAINING DATA
####____________________________________________________
print('Merging training data...')
start_time = time.time()

# Create empty list to store results
surficial_data_list = []

for name in surficial_features:
    # Define input dataset
    name_value = surficial_dictionary.get(name)
    training_input = f'{region}_Training_{name.title().replace(" ", "")}_3338'

    # Load the surficial feature points from the geodatabase
    surficial_data = gpd.read_file(geodatabase, layer=training_input)

    # Sample the surficial data to 200 rows
    sample_size = min(200, len(surficial_data))
    surficial_data = surficial_data.sample(n=sample_size, random_state=42)

    # Add the constant value field
    surficial_data['surficial'] = name_value

    # Create cent_x and cent_y fields
    surficial_data['cent_x'] = surficial_data.geometry.x
    surficial_data['cent_y'] = surficial_data.geometry.y
    surficial_data = surficial_data[['cent_x', 'cent_y', 'surficial']]

    # Append the GeoDataFrame to our list
    surficial_data_list.append(surficial_data)

# Concatenate all dataframes in the list into the final DataFrame
if surficial_data_list:
    surficial_data = pd.concat(surficial_data_list, ignore_index=True)
else:
    surficial_data = pd.DataFrame()

# Export surficial training data to csv
surficial_data.to_csv(surficial_output, index=False)
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
    blob.upload_from_filename(surficial_output)
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
