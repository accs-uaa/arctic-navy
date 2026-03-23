# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Train transfer models
# Author: Timm Nawrocki
# Last Updated: 2026-03-20
# Usage: Must be executed in a Python 3.12+ installation.
# Description: 'Train transfer models' trains and predicts transfer models for each foliar cover map.
# ---------------------------------------------------------------------------

# Define region
region = 'McIntyre'

# Import packages
import ee
import time
from akutils import *

#### SET UP ENVIRONMENT
####____________________________________________________

# Define GEE paths
ee_project = 'accs-geospatial-processing'
asset_prefix = 'arctic_navy'
asset_path = f'projects/{ee_project}/assets/{asset_prefix}'
image_path = f'{asset_path}/image_data/{region}_Imagery_20220803_0p5m_3338'
coast_path = f'{asset_path}/distance_data/{region}_Coastal_Distance_0p5m_3338'

# Define GCS paths
storage_bucket = 'arctic-navy'

# Create input list for foliar cover maps
foliar_list = ['bromos', 'dryas', 'dsalix', 'erivag', 'halgra',
               'ndsalix', 'nerishr', 'sphagn', 'watercor', 'wetsed']

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
training_data = ee.FeatureCollection(f'{asset_path}/training_data/{region}_TransferSample_Covariates')
study_area = ee.FeatureCollection(f'{asset_path}/region_data/{region}_StudyArea_3338')

# Create image collection
covariate_image = image_data

#### TRAIN AND PREDICT TRANSFER MODEL
####____________________________________________________

# Extract band names
band_names = covariate_image.bandNames()

# Drop any rows with null values
training_clean = training_data.filter(ee.Filter.notNull(band_names))
clean_count = training_clean.size().getInfo()
print(f'Total training points after removing nulls: {clean_count}.')

# Create a model for each diagnostic species set
for name in foliar_list:
    print(f'Training and evaluating regressor for {name}...')
    start_time = time.time()

    # Split the presence and absence data
    presence = training_clean.filter(ee.Filter.gt(name, 0))
    absence = training_clean.filter(ee.Filter.eq(name, 0))

    # Count the presence rows and define absence number
    presence_count = presence.size().getInfo()
    target_absence = presence_count * 5

    # Subsample absence points
    print(f'\t{presence_count} presence samples. '
          f'Subsampling absences to max {min(target_absence, (clean_count - presence_count))}...')
    absence_subsample = absence.randomColumn('random').sort('random').limit(target_absence)

    # Merge training data
    if presence_count >= 50000:
        # Limit presence number if greater than 50,000
        presence_subsample = presence.randomColumn('random').sort('random').limit(50000)
        training_balanced = presence_subsample.merge(absence_subsample)
    else:
        training_balanced = presence.merge(absence_subsample)

    # Count the final number of rows
    n_rows = training_balanced.size().getInfo()
    print(f'\tTraining samples includes {n_rows} rows...')

    # Train a regressor
    print('\tTraining regressor on train partition...')
    regressor = ee.Classifier.smileRandomForest(
        numberOfTrees=50,
        minLeafPopulation=5
    ).setOutputMode('REGRESSION').train(
        features=training_balanced,
        classProperty=name,
        inputProperties=band_names
    )

    # Predict model for input image
    print(f'\tApplying {name} model to imagery...')
    predicted_image = covariate_image.classify(regressor).clamp(0, 100).toByte()

    # Export prediction to cloud storage
    image_task = ee.batch.Export.image.toCloudStorage(
        image=predicted_image,
        description=f'{region.lower()}-map-{name}',
        bucket=storage_bucket,
        fileNamePrefix=f'foliar_data/{region}_{name}_0.5m_3338',
        region=study_area.geometry(),
        scale=0.5,
        crs='EPSG:3338',
        maxPixels=1e13,
        formatOptions={'cloudOptimized': True}
    )
    image_task.start()
    print(f'\tInitiated prediction export for {name}.')
    end_timing(start_time)
