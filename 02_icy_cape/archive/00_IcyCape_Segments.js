// 1. SETUP ANALYSIS

// Import assets
var segmentation_image = ee.Image("projects/akveg-map/assets/navy_arctic/IcyCape_CIR_0p5m_3338");

// Add image asset to map
var cirVis = {
  min: 0,
  max: 254,
  bands: ['b1', 'b2', 'b3']
};
Map.addLayer(segmentation_image, cirVis, 'Segmentation Composite');

// 3. CREATE SEGMENTS

// Select subset of the composite for clustering
print(segmentation_image.bandNames())

// Prepare convoluted image
var kernel = ee.Kernel.gaussian(3);
var convoluted_image = segmentation_image.convolve(kernel); // Question: is this running at 0.5 m? Produce an intermediate 2 m dataset for segments.

// Set seed grid
var seeds = ee.Algorithms.Image.Segmentation.seedGrid(12);

// Execute Simple Non-Iterative Clustering
var segments = ee.Algorithms.Image.Segmentation.SNIC({
  image: convoluted_image,
  size: 2,
  compactness: 0,
  connectivity: 4,
  neighborhoodSize: 512,
  seeds: seeds
}).reproject({
  crs: 'EPSG:3338',
  scale: 2
}).select(
  ['b1_mean', 'b2_mean', 'b3_mean', 'clusters'],
  ['b1', 'b2', 'b3', 'clusters']);
var clusters = segments.select('clusters')

// Add RGB composite and clusters to the map.
//Map.addLayer(convoluted_image, rgbVis, 'Convoluted Composite');
Map.addLayer(clusters.randomVisualizer(), {}, 'clusters')

// Define export parameters
Export.image.toCloudStorage({
  image: clusters,
  description: 'IcyCape_Segments',
  bucket: 'akveg-data',
  fileNamePrefix: 'navy_arctic/IcyCape_Segments_v2_2m_3338.tif',
  region: segmentation_image.geometry(),
  scale: 2,
  crs: 'EPSG:3338',
  maxPixels: 1e13,
  formatOptions: {
    cloudOptimized: true
  }
});