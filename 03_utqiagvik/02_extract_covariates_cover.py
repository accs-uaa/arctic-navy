# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Extract covariates cover transfer
# Author: Timm Nawrocki
# Last Updated: 2026-03-20
# Usage: Must be executed in a Python 3.12+ installation.
# Description: "Extract covariates cover transfer" extracts covariate data to the sample points containing the sampled foliar cover data for transfer learning.
# ---------------------------------------------------------------------------

# Define region
region = 'Utqiagvik'

# Import packages
import ee

#### SET UP ENVIRONMENT
####____________________________________________________

# Define GEE paths
ee_project = 'accs-geospatial-processing'
asset_prefix = 'arctic_navy'
asset_path = f'projects/{ee_project}/assets/{asset_prefix}'
image_path = f'{asset_path}/image_data/{region}_Imagery_20240710_0p5m_3338'
coast_path = f'{asset_path}/distance_data/{region}_Coastal_Distance_0p5m_3338'

# Authenticate Earth Engine
print('Connecting to Earth Engine server...')
try:
    ee.Initialize(project=ee_project)
except Exception as e:
    print('Prompting authentication...')
    ee.Authenticate()
    ee.Initialize(project=ee_project)

# Define input data
image_data = ee.Image(image_path)
coast_data = ee.Image(coast_path).rename(['coast'])
training_points = ee.FeatureCollection(f'{asset_path}/training_data/{region}_TransferSample')
training_points = training_points.filter(ee.Filter.notNull(['.geo']))

# Create image collection
covariate_image = image_data \
    .addBands(coast_data)

#### BUFFER AND SAMPLE POINTS
####____________________________________________________

# Create 4 m buffers around each point
def buffer_points(feature):
    return feature.buffer(4)
buffered_points = training_points.map(buffer_points)

# Extract band means within the buffers
training_data = covariate_image.reduceRegions(
    collection=buffered_points,
    reducer=ee.Reducer.mean(),
    scale=1,
    tileScale=16
)

# Create an export task for the sampling reduction
task = ee.batch.Export.table.toAsset(
    collection=training_data,
    description=f'{region.lower()}-transfer-covariates',
    assetId=f'{asset_path}/training_data/{region}_TransferSample_Covariates'
)

# Initiate task
task.start()
print(f'Export task for initiated.')
