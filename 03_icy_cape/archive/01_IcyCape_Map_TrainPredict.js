// 1. SETUP ANALYSIS

// Import assets
var segmentation_image = ee.Image('projects/akveg-map/assets/navy_arctic/IcyCape_CIR_0p5m_3338');
var training_points = ee.FeatureCollection('projects/akveg-map/assets/navy_arctic/IcyCape_Training_v2_3338')

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
  properties: ['label'],
  scale: 0.5,
  tileScale: 16
});

// 3. TRAIN RANDOM FOREST MODEL

// Train Random Forest classifier
var classifier = ee.Classifier.smileRandomForest({
  numberOfTrees: 500
})
.train({
  features: training_data,
  classProperty: 'label',
  inputProperties: segmentation_image.bandNames()
});


// 4. PREDICT (CLASSIFY)

// Classify the image using the trained model
var classified_image = segmentation_image.classify(classifier);


// 5. VISUALIZATION

// Define a palette for the 8 classes
var palette = [
  '#1f77b4', // Class 1 (e.g., Water) - Blue
  '#aec7e8', // Class 2 - Light Blue
  '#ff7f0e', // Class 3 - Orange
  '#2ca02c', // Class 4 - Green
  '#98df8a', // Class 5 - Light Green
  '#d62728', // Class 6 - Red
  '#9467bd',  // Class 7 - Purple
  '#FFFFFF'  // Class 8 - White
];

Map.addLayer(classified_image, {min: 1, max: 8, palette: palette}, 'Classified');

// Center the map on the training points to see the result
Map.centerObject(training_points, 14);

// Define export parameters
Export.image.toCloudStorage({
  image: classified_image.toByte(),
  description: 'IcyCape_Classification',
  bucket: 'akveg-data',
  fileNamePrefix: 'navy_arctic/IcyCape_Classified_v2_0.5m_3338.tif',
  region: segmentation_image.geometry(),
  scale: 0.5,
  crs: 'EPSG:3338',
  maxPixels: 1e13,
  formatOptions: {
    cloudOptimized: true
  }
});