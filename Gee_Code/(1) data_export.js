var gediz = ee.FeatureCollection("projects/ee-bau-tubitak-ndvi/assets/DestekParselleri");
var sentinel_Collection = ee.ImageCollection("COPERNICUS/S2_SR");
var year = 2018

//add ndvi
function add_NDVI(input) {
  var nd = input.normalizedDifference(["B8", "B4"]).rename("ndvi");
  return input.addBands(nd);
}

//gather image data
function get_monthly_ImageCollection() 
{
  var imageCollection = ee.ImageCollection([]);

  for (var month = 1; month <= 12; month++) 
  {
    var start_date = ee.Date.fromYMD(year, month, 1);
    var end_date = start_date.advance(1, "month");
    
    var dataset = ee.ImageCollection("COPERNICUS/S2")
      .filterDate(start_date, end_date)
      .map(add_NDVI)
      .median()
      .select("ndvi");
      
    var image = dataset.set("month", (month).toString());
    imageCollection = imageCollection.merge(ee.ImageCollection([image]));
  }
  return imageCollection;
}

//create empty featurecollection with tarimparse and mean ndvi list
function featureCollection_init(feature) {
  var tarimParse = feature.get("TarimParse");
  var geometry = feature.geometry();
  return ee.Feature(geometry).set("TarimParse", tarimParse).set("mean_ndvi", []);
}


//collect data from images
function collect_data(image, database) 
{
  return database.map(function (feature) 
  {
    var mean_ndvi = image.reduceRegion(
    {
      reducer: ee.Reducer.mean(),
      geometry: feature.geometry(),
      scale: 30,
      maxPixels: 1e9
    }).get("ndvi");
    
    var mean_ndvi_array = ee.List(feature.get("mean_ndvi"));
    mean_ndvi_array = mean_ndvi_array.add(mean_ndvi);
    return feature.set("mean_ndvi", mean_ndvi_array);
  });
}


//Run
var monthlyImageCollection = get_monthly_ImageCollection();
var database = gediz.distinct("TarimParse").map(featureCollection_init);
var monthlyImages = monthlyImageCollection.toList(monthlyImageCollection.size());
for (var month = 0; month < monthlyImageCollection.size().getInfo(); month++) 
{
    var image = ee.Image(monthlyImages.get(month));
    database = collect_data(image, database);
}


//export
Export.table.toDrive({
  collection:results,
  description:"Ndvi_export",
  folder:"gee_ndvi",
  fileNamePrefix:"data",
  fileFormat:"CSV"
});