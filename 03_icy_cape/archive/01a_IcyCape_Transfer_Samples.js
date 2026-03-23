// Import assets
var icycape_image = ee.Image.loadGeoTIFF('gs://akveg-data/vhr/vhr_cogs_snap/PS_SRLite_00p50m_20200714_220835_WV02_10300100AB37D700_cog.tif');
var training_points = ee.FeatureCollection('projects/akveg-map/assets/navy_arctic/IcyCape_erivag_10m')

// Add image asset to map
var vis_nrg_4band = {bands:['b04_nir', 'b03_red', 'b02_green'], min:0, max:[5000, 2000, 2000]};
Map.addLayer(icycape_image, vis_nrg_4band, 'Icy Cape');

// Print metadata on segmentation image
print(icycape_image)

// 2. EXTRACT DATA (SAMPLING)

// Extract pixel values to point feature class
var training_data = icycape_image.sampleRegions({
  collection: training_points,
  properties: ['cover'],
  scale: 0.5,
  tileScale: 16
});

// 3. EXPORT TO ASSET
// This saves the "work" of looking at the pixels.
Export.table.toAsset({
  collection: training_data,
  description: 'icycape-transfer',
  assetId: 'projects/akveg-map/assets/IcyCape_Transfer_Covariates'
});