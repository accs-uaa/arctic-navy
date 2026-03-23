# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Extract covariates for surficial features
# Author: Timm Nawrocki
# Last Updated: 2026-03-20
# Usage: Must be executed in a Python 3.12+ installation.
# Description: "Extract covariates for surficial features" extracts covariate data to the surficial feature sample points.
# ---------------------------------------------------------------------------

# Define region
region = 'McIntyre'

# Import packages
import ee

#### SET UP ENVIRONMENT
####____________________________________________________

# Define GEE paths
ee_project = 'accs-geospatial-processing'
asset_prefix = 'arctic_navy'
asset_path = f'projects/{ee_project}/assets/{asset_prefix}'
image_path = f'{asset_path}/image_data/{region}_Imagery_20220803_0p5m_3338'
coast_path = f'{asset_path}/distance_data/{region}_Coastal_Distance_0p5m_3338'
salt_path = f'{asset_path}/distance_data/{region}_SaltIntruded_Distance_0p5m_3338'

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
salt_data = ee.Image(salt_path).rename(['salt'])
training_points = ee.FeatureCollection(f'{asset_path}/training_data/{region}_SurficialPoints')
training_points = training_points.filter(ee.Filter.notNull(['.geo']))

# Create image collection
covariate_image = image_data \
    .addBands(coast_data) \
    .addBands(salt_data)

#### SAMPLE POINTS
####____________________________________________________

# Extract bands to the points
training_data = covariate_image.sampleRegions(
    collection=training_points,
    scale=0.5,
    tileScale=16,
    geometries=True
)

# Create an export task for the sampling reduction
task = ee.batch.Export.table.toAsset(
    collection=training_data,
    description=f'{region.lower()}-surficial-covariates',
    assetId=f'{asset_path}/training_data/{region}_SurficialPoints_Covariates'
)

# Initiate task
task.start()
print(f'Export task for initiated.')
