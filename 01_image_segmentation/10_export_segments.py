# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Export image segments
# Author: Timm Nawrocki
# Last Updated: 2026-03-20
# Usage: Must be executed in a Python 3.12+ installation.
# Description: 'Export image segments' exports previously created image segments for three Arctic Navy Installations to Google Cloud Storage.
# ---------------------------------------------------------------------------

# Import packages
import ee
import os

#### SET UP ENVIRONMENT
####____________________________________________________

# Define GEE paths
ee_project = 'akveg-map'
asset_prefix = 'segments'
asset_path = f'projects/{ee_project}/assets/{asset_prefix}/SNIC_segmentation_final'
area_path = f'projects/{ee_project}/assets/arctic_navy/region_data'

# Define GCS paths
storage_bucket = 'arctic-navy'
export_folder = 'segment_data'

# Authenticate Earth Engine
print('Connecting to Earth Engine server...')
try:
    ee.Initialize(project=ee_project)
except Exception as e:
    print('Prompting authentication...')
    ee.Authenticate()
    ee.Initialize(project=ee_project)

#### EXPORT SEGMENTS
####____________________________________________________

# Load segments
segment_collection = ee.ImageCollection(asset_path)

# Get a list of the segment image IDs (system:index)
segment_names = segment_collection.aggregate_array('system:index').getInfo()

# Loop through the segment names
for segment_name in segment_names:
    # Get the single segment image
    segment_image = segment_collection.filter(ee.Filter.eq('system:index', segment_name)).first()

    # Define export name
    if 'icycape' in segment_name.lower():
        export_path = f'{export_folder}/IcyCape_Segments_2m_3338'
        task_name = 'icycape-segment-export'
        study_area = ee.FeatureCollection(f'{area_path}/IcyCape_StudyArea')
    elif 'utqiagvik' in segment_name.lower():
        export_path = f'{export_folder}/Utqiagvik_Segments_2m_3338'
        task_name = 'utqiagvik-segment-export'
        study_area = ee.FeatureCollection(f'{area_path}/Utqiagvik_StudyArea')
    elif 'kuparuk' in segment_name.lower():
        export_path = f'{export_folder}/McIntyre_Segments_2m_3338'
        task_name = 'mcintyre-segment-export'
        study_area = ee.FeatureCollection(f'{area_path}/McIntyre_StudyArea')
    else:
        print('ERROR: Check input feature name.')
        quit()

    # Define export task to Google Cloud Storage
    task = ee.batch.Export.image.toCloudStorage(
        image=segment_image,
        description=task_name,
        bucket=storage_bucket,
        fileNamePrefix=export_path,
        scale=2,
        crs='EPSG:3338',
        region=study_area.geometry(),
        maxPixels=1e13,
        formatOptions={'cloudOptimized': True}
    )

    # Start the task on the Earth Engine servers
    task.start()
    print(f'Task submitted: {os.path.basename(export_path)}')
