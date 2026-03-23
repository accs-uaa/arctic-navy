# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Create study areas
# Author: Timm Nawrocki
# Last Updated: 2026-03-02
# Usage: Must be executed in a Python 3.12+ installation.
# Description: "Create study areas" converts the valid data regions from each processed image strip into a study area per Naval installation.
# ---------------------------------------------------------------------------

# Import packages
import ee

#### SET UP ENVIRONMENT
####____________________________________________________

# Define paths
ee_project = 'akveg-map'
storage_bucket = 'akveg-data'
export_prefix = 'navy_arctic'

# Authenticate with Earth Engine
print('Requesting information from server...')
ee.Authenticate()
ee.Initialize(project=ee_project)

# Define asset path
asset_path = f'projects/{ee_project}/assets'

# Define data paths
image_path = f'gs://{storage_bucket}/vhr/vhr_cogs_snap'
icycape_input = f'{image_path}/MS_SRLite_02p00m_20200714_220835_WV02_10300100AB37D700_cog.tif'
utqiagvik_input = f'{image_path}/MS_SRLite_02p00m_20240710_222652_WV03_10400100996FB100_cog.tif'
kuparuk_input = f'{image_path}/MS_SRLite_02p00m_20220803_213641_WV03_10400100786F6C00_cog.tif'

# Define study area names
name_dictionary = {icycape_input: 'Icy Cape',
                   utqiagvik_input: 'Utqiagvik',
                   kuparuk_input: 'Kuparuk'}

#### EXPORT VALID DATA REGIONS
####____________________________________________________

for raster_input in [icycape_input, utqiagvik_input, kuparuk_input]:
    # Load raster data to images
    image = ee.Image.loadGeoTIFF(raster_input)
    site_name_server = ee.String(name_dictionary.get(raster_input))
    site_name_client = name_dictionary.get(raster_input)

    # Create a valid data mask
    mask = image.select(0).mask().selfMask()

    # Sample points within the valid data mask
    sampled_points = mask.sample(
        region=image.geometry(1).bounds(1),
        scale=100,
        numPixels=100000,
        geometries=True
    )

    # Calculate a convex hull study area from the sampled points
    study_area = sampled_points.geometry().convexHull()
    vector_geometry = study_area.buffer(-500).simplify(10).transform('EPSG:3338', 1)

    # Construct the feature collection for export
    export_feature = ee.Feature(vector_geometry).set('site_name', site_name_server)
    export_collection = ee.FeatureCollection(export_feature)

    # Initiate task
    export_name = site_name_client.replace(" ", "")
    vector_task = ee.batch.Export.table.toCloudStorage(
        collection=export_collection,
        description=f'{export_name.lower()}-study-area',
        bucket=storage_bucket,
        fileNamePrefix=f'{export_prefix}/{export_name}_StudyArea',
        fileFormat='SHP'
    )

    vector_task.start()
    print(f'Export task for {site_name_client} initiated.')
