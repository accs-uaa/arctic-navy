# ---------------------------------------------------------------------------
# Parse water training data
# Author: Timm Nawrocki, Alaska Center for Conservation Science
# Last Updated: 2026-03-05
# Usage: Must be executed in a Python 3.12+ installation.
# Description: "Parse water training data" parses ground cover observations for sub-canopy surface water percentage.
# ---------------------------------------------------------------------------

# Import libraries
import ee
import os
import time
import numpy as np
import pandas as pd
from google.cloud import storage
from akutils import *

# Set version date
version_date = '20260212'

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/AKVEG_Map')
input_folder = os.path.join(project_folder, 'Data/Data_Input/database_archive', f'version_{version_date}')
output_folder = os.path.join(drive, root_folder,
                             'Projects/VegetationEcology/DoD_Navy_Arctic',
                             'Data/Data_Input/water_data')

# Define input files
site_visit_input = os.path.join(input_folder, '03_site_visit.csv')
abiotic_input = os.path.join(input_folder, '06_abiotic_cover.csv')
ground_input = os.path.join(input_folder, '08_ground_cover.csv')

# Define output file
water_output = os.path.join(output_folder, 'AKVEG_Water_3338.csv')

# Define paths
ee_project = 'akveg-map'
storage_bucket = 'akveg-data'
export_prefix = 'arctic_navy'
file_name = os.path.basename(water_output)
storage_path = f'arctic_navy/surficial_data/{file_name}'
asset_path = f'projects/{ee_project}/assets'

# Define asset
gcs_uri = f'gs://{storage_bucket}/{storage_path}'
asset_id = f'{asset_path}/{export_prefix}/AKVEG_Water'

#### READ AND PREPARE INPUT DATA
####____________________________________________________
print('Parsing water observations from AKVEG Database...')
start_time = time.time()

# Read input data
site_visit_data = pd.read_csv(site_visit_input)
abiotic_data = pd.read_csv(abiotic_input)
ground_data = pd.read_csv(ground_input)

# Limit observations to water
abiotic_data = abiotic_data[abiotic_data['abiotic_element'] == 'water']
ground_data = ground_data[ground_data['ground_element'] == 'water']

# Merge ground and abiotic observations
abiotic_data = abiotic_data[~abiotic_data['site_visit_code'].isin(ground_data['site_visit_code'].unique())]
water_data = pd.concat([abiotic_data, ground_data], axis=0)

# Exclude site visits sampled before 2000
site_visit_data = site_visit_data[site_visit_data['observe_year'] >= 2000]

# Exclude site visits where the plot radius is below 4 m
site_visit_data = site_visit_data[site_visit_data['plot_radius_m'] >= 4]

# Exclude earlier revisits to the most recent site visit
revisit_data = site_visit_data.copy()
site_counts = revisit_data['site_code'].value_counts()
revisit_data['total_visits'] = revisit_data['site_code'].map(site_counts)
revisit_data['observe_datetime'] = pd.to_datetime(revisit_data['observe_date'], format='%Y-%m-%d')
revisit_data = revisit_data.sort_values(by='observe_datetime')
revisit_data = revisit_data.drop_duplicates(subset=['site_code'], keep='last')
revisit_data = revisit_data.drop(columns=['observe_datetime', 'total_visits']).copy()
site_visit_data['exclude'] = np.where(
    site_visit_data['site_visit_code'].isin(revisit_data['site_visit_code'].unique()),
    0, 1)
site_visit_data = site_visit_data[site_visit_data['exclude'] == 0]

# Identify sites with abiotic top cover
site_visit_data = site_visit_data[site_visit_data['site_visit_code'].isin(
    water_data['site_visit_code'].unique()
)]

# Join the abiotic data to the site visits
water_data = pd.merge(left=site_visit_data,
                      right=water_data,
                      on='site_visit_code',
                      how='left')

# Export data to csv
water_data.to_csv(water_output, header=True, index=False, sep=',', encoding='utf-8')
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
    blob.upload_from_filename(water_output)
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
