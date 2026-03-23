# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Train surficial features model
# Author: Timm Nawrocki
# Last Updated: 2026-03-20
# Usage: Must be executed in a Python 3.12+ installation.
# Description: 'Train surficial features model' trains a Random Forest model to predict surficial features.
# ---------------------------------------------------------------------------

# Define region
region = 'Utqiagvik'

# Import packages
import ee
import os
import time
from akutils import *

#### SET UP ENVIRONMENT
####____________________________________________________

# Define GEE paths
ee_project = 'accs-geospatial-processing'
asset_prefix = 'arctic_navy'
asset_path = f'projects/{ee_project}/assets/{asset_prefix}'
image_path = f'{asset_path}/image_data/{region}_Imagery_20240710_0p5m_3338'
coast_path = f'{asset_path}/distance_data/{region}_Coastal_Distance_0p5m_3338'

# Define GCS paths
storage_bucket = 'arctic-navy'

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
training_data = ee.FeatureCollection(f'{asset_path}/training_data/{region}_SurficialPoints_Covariates')
study_area = ee.FeatureCollection(f'{asset_path}/region_data/{region}_StudyArea_3338')

# Create image collection
covariate_image = image_data \
    .addBands(coast_data)

#### TRAIN AND PREDICT SURFICIAL MODEL
####____________________________________________________

# Train the Random Forest classifier
print('Training Random Forest classifier...')
classifier = ee.Classifier.smileRandomForest(numberOfTrees=100).train(
    features=training_data,
    classProperty='surficial',
    inputProperties=covariate_image.bandNames()
)

# Classify the image using the trained model
print('Classifying image...')
classified_image = covariate_image.classify(classifier)

# Define export parameters
print('Configuring export task...')
task = ee.batch.Export.image.toCloudStorage(
    image=classified_image.toByte(),
    description=f'{region.lower()}-surficial',
    bucket=storage_bucket,
    fileNamePrefix=f'surficial_data/{region}_Surficial_0.5m_3338',
    region=study_area.geometry(),
    scale=0.5,
    crs='EPSG:3338',
    maxPixels=1e13,
    formatOptions={'cloudOptimized': True}
)

# Initiate task
task.start()
print('Initiated prediction export for surficial features.')
