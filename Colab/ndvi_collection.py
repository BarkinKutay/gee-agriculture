import ee

ee.Initialize(project="ee-bau-tubitak-ndvi")
parsel_data = ee.FeatureCollection("projects/ee-bau-tubitak-ndvi/assets/DestekParselleri")
image_data = ee.ImageCollection("COPERNICUS/S2")
year = 2018
count = 50
month_range = 12

def add_ndvi(input_image):
    nd = input_image.normalizedDifference(["B8", "B4"]).rename("ndvi")
    return input_image.addBands(nd)

def get_monthly_ImageCollection(year): 

    imageCollection = ee.ImageCollection([])

    for month in range(month_range):
        start_date = ee.Date.fromYMD(year, month+1, 1)
        end_date = start_date.advance(1, "month")

        image = (image_data 
            .filterDate(start_date, end_date)
            .map(add_ndvi)
            .median()
            .select("ndvi"))
        
        image = image.set("month", str(month))
        imageCollection = imageCollection.merge(ee.ImageCollection([image]))

    return imageCollection

def featureCollection_init(feature):
    tarimParse = feature.get("TarimParse")
    geometry = feature.geometry()
    return ee.Feature(geometry).set("TarimParse", tarimParse).set("mean_ndvi", [])

def collect_data(image, database):

    def map_function(feature):
        mean_ndvi = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=feature.geometry(),
            scale=30,
            maxPixels=1e9
        ).get("ndvi")
        
        mean_ndvi_array = ee.List(feature.get("mean_ndvi"))
        mean_ndvi_array = mean_ndvi_array.add(mean_ndvi)
        feature = feature.set("mean_ndvi", mean_ndvi_array)
        return feature
    
    return database.map(map_function)



database = parsel_data.distinct("TarimParse").limit(count).map(featureCollection_init)

image_collection = get_monthly_ImageCollection(year)
image_list = image_collection.toList(month_range)

for month in range(image_list.size().getInfo()):
    image = ee.Image(image_list.get(month))
    database = collect_data(image, database)


export_params = {
    'collection': database,
    'description': "py_export",
    'folder': "dosya_1",
    'fileNamePrefix': "py_export",
    'fileFormat': 'CSV'
}

task = ee.batch.Export.table.toDrive(**export_params)
task.start()