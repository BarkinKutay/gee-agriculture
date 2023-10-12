var gediz = ee.FeatureCollection("projects/ee-bau-tubitak-ndvi/assets/DestekParselleri");

function calculateBSI(image) {
  var BLUE = image.select('B2');
  var RED = image.select("B4");
  var NIR = image.select("B8");
  var SWIR = image.select('B11');
  //  let val = 2.5 * ((s.B11 + s.B04)-(s.B08 + s.B02))/((s.B11 + s.B04)+(s.B08 + s.B02));
  
  var BSI = ((SWIR.add(RED)).subtract(NIR.add(BLUE))).divide((SWIR.add(RED)).add(NIR.add(BLUE)));
  var BSI_scaled = BSI.multiply(2.5).rename('bsi');

  return image.addBands(BSI_scaled);
}
// datatsetler bsi ve rgb için

var dataset = ee.ImageCollection("COPERNICUS/S2")
  .filterBounds(gediz)
  .filterDate("2020-01-01","2020-02-02")
  .map(calculateBSI)
  .median()
  .select("bsi"); 

var dataset2 = ee.ImageCollection("COPERNICUS/S2")
  .filterBounds(gediz)
  .filterDate("2020-04-04","2020-05-05")
  .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', 10)
  .median()

var datasetc = dataset.clip(gediz)
var datasetc2 = dataset2.clip(gediz)


var bsiPalette = ['00ee00', '006400', 'ff3030', 'cd5555', 'ffff00'];
// 
Map.addLayer(datasetc, {
  min: -1,
  max: 1,
  palette: bsiPalette
}, 'Bare Soil Index');

var S2_display = {bands: ['B4', 'B3', 'B2'], min: 0, max: 3000};

Map.addLayer(datasetc2,S2_display,'Sentinel 2 RGB')
Map.centerObject(gediz,13)
