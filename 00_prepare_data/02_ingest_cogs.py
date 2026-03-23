# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Ingest cloud-optimized geotiffs
# Author: Timm Nawrocki
# Last Updated: 2026-01-20
# Usage: Must be executed in a Python 3.12+ installation.
# Description: "Ingest cloud-optimized geotiffs" ingests cloud-optimized geotiffs for covariates into GEE.
# ---------------------------------------------------------------------------

# Import packages
import ee
import os
import re
from google.cloud import storage

#### SET UP GEE ENVIRONMENT
####____________________________________________________

# Define paths
ee_project = 'accs-geospatial-processing'
storage_bucket = 'arctic-navy'
image_prefix = 'image_data'
distance_prefix = 'distance_data'

# Create list of folders to process
folder_list = [image_prefix, distance_prefix]

# Authenticate with Earth Engine
print('Requesting information from server...')
ee.Authenticate()
ee.Initialize(project=ee_project)

# Initialize GCS client once
client = storage.Client(project=ee_project)

#### INGEST COGS INTO GEE
####____________________________________________________

# Create assets for each geotiff
for storage_prefix in folder_list:
    print(f"\n#### Processing folder: {storage_prefix} ####")
    print('-------------------------------------------')

    # Get list of files from Google Cloud Storage for the storage prefix
    blobs = client.list_blobs(storage_bucket, prefix=storage_prefix)

    # Filter the list to geotiffs in the specific folder
    reg = re.compile(r'^' + storage_prefix + r'/.*\.tif$')
    geotiff_list = [blob.name for blob in blobs if reg.search(blob.name)]
    print(f"Found {len(geotiff_list)} geotiffs in GCS for '{storage_prefix}'.")

    # Ensure the parent folder exists in GEE
    parent_asset_id = f'projects/{ee_project}/assets/arctic_navy/{storage_prefix}'
    try:
        ee.data.getAsset(parent_asset_id)
        print(f"Parent asset found: {parent_asset_id}")
    except ee.EEException:
        print(f"Parent asset not found. Creating ImageCollection: {parent_asset_id}")
        ee.data.createAsset(
            {'type': 'FOLDER'},
            parent_asset_id
        )

    # Check for and avoid duplicates
    existing_assets = []
    try:
        assets_response = ee.data.listAssets({'parent': parent_asset_id})
        if 'assets' in assets_response:
            for asset in assets_response['assets']:
                existing_assets.append(os.path.basename(asset['name']) + '.tif')
    except ee.EEException as e:
        print(f"Error listing assets (folder might be empty): {e}")

    # Send ingestion request for each geotiff in the storage prefix
    for geotiff in geotiff_list:
        # Define file name
        file_name = os.path.basename(geotiff)
        # Define the target asset ID
        asset_name = os.path.splitext(file_name)[0]
        full_asset_id = f'{parent_asset_id}/{asset_name}'

        # Ingest asset if it does not already exist
        if file_name not in existing_assets:
            print(f'Ingesting {file_name} as a COG-backed asset...')

            # Request body using the Python Client syntax
            request = {
                'type': 'IMAGE',
                'gcs_location': {
                    'uris': [f'gs://{storage_bucket}/{geotiff}']
                },
                'properties': {
                    'source': 'https://github.com/accs-uaa/akveg-map',
                    'original_filename': file_name
                },
                'startTime': '2026-01-01T00:00:00Z',
                'endTime': '2026-12-31T15:01:23Z',
            }

            try:
                # Use the native library method instead of manual requests
                ee.data.createAsset(request, full_asset_id)
                print(f'\tSuccessfully created: {full_asset_id}')
            except ee.EEException as e:
                print(f'\tFailed to create {file_name}: {e}')

        else:
            print(f'{file_name} already exists. Skipping.')
