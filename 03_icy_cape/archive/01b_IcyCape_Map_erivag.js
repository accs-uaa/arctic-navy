// 1. SETUP ANALYSIS

// Import assets
var segmentation_image = ee.Image('projects/akveg-map/assets/navy_arctic/IcyCape_CIR_0p5m_3338');
var training_points = ee.FeatureCollection('projects/akveg-map/assets/navy_arctic/IcyCape_erivag_3338')

// Add image asset to map
var cirVis = {
  min: 0,
  max: 254,
  bands: ['b1', 'b2', 'b3']
};
Map.addLayer(segmentation_image, cirVis, 'Segmentation Composite');

// Print metadata on segmentation image
print(segmentation_image)

// 2. EXTRACT DATA (SAMPLING)

// Extract pixel values to point feature class
var training_data = segmentation_image.sampleRegions({
  collection: training_points,
  properties: ['grid_code'],
  scale: 0.5,
  tileScale: 16
});

// 3. TRAIN RANDOM FOREST MODEL

// Train Random Forest classifier
var regressor = ee.Classifier.smileRandomForest({
  numberOfTrees: 100
})
.setOutputMode('REGRESSION')
.train({
  features: training_data,
  classProperty: 'grid_code',
  inputProperties: segmentation_image.bandNames()
});


// 4. PREDICT (REGRESS)

// Classify the image using the trained model
var regressed_image = segmentation_image.classify(regressor);


// 5. VISUALIZATION

// Define a palette for the 8 classes
var regressionVis = {
  min: 0,
  max: 20,
  palette: [
    '#aec7e8',
    '#1f77b4',
    '#d62728'
  ]
};
Map.addLayer(regressed_image, regressionVis, 'erivag');

// Center the map on the training points to see the result
Map.centerObject(training_points, 14);

// Define export parameters
Export.image.toCloudStorage({
  image: regressed_image.toByte(),
  description: 'IcyCape_Regress_erivag',
  bucket: 'akveg-data',
  fileNamePrefix: 'navy_arctic/IcyCape_erivag_0.5m_3338.tif',
  region: segmentation_image.geometry(),
  scale: 0.5,
  crs: 'EPSG:3338',
  maxPixels: 1e13,
  formatOptions: {
    cloudOptimized: true
  }
});