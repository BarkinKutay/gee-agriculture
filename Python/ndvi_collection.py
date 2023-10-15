import ee
import pandas as pd
import math
import time
import credentials

user = credentials.user()

ee.Initialize(project=user.project_id)

parsel_data = ee.FeatureCollection(user.parcel_data_id)

image_data = ee.ImageCollection("COPERNICUS/S2")
year = 2018
month_range = 12
count = None

batch_size = 1000


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

def data_conversion(df):
    df["peak_month"] = df["mean_ndvi"].apply(lambda x: x.index(max(x)) + 1)
    df["peak_list"] = df["mean_ndvi"].apply(Peak_List)
    df["peak_count"] = df["peak_list"].apply(lambda x: len(x))

def Peak_List(parsel_ndvi):
    peaks = []
    for month in range(len(parsel_ndvi)):
        if month == 0:
            if parsel_ndvi[month] > parsel_ndvi[month + 1]:
                peaks.append(month + 1)
        elif month == len(parsel_ndvi) - 1:
            if parsel_ndvi[month] > parsel_ndvi[month - 1]:
                peaks.append(month + 1)
        else:
            if parsel_ndvi[month] > parsel_ndvi[month - 1] and parsel_ndvi[month] > parsel_ndvi[month + 1]:
                peaks.append(month + 1)
    return peaks

def batch_processing(image_list, database, batch_num):
    data_list = []

    for month in range(image_list.size().getInfo()):
        image = ee.Image(image_list.get(month))
        database = collect_data(image, database)

    for feature in database.getInfo()["features"]:
        properties = feature["properties"]
        properties[".geo"] = feature["geometry"]
        data_list.append(properties)

    df = pd.DataFrame(data_list)
    data_conversion(df)

    column_to_move = df.pop(".geo")
    df.insert(len(df.columns), ".geo", column_to_move)

    return df

database = parsel_data.distinct("TarimParse").limit(count).map(featureCollection_init)

image_collection = get_monthly_ImageCollection(year)
image_list = image_collection.toList(month_range)

merged_df = pd.DataFrame()

total_batches = math.ceil(database.size().getInfo() / batch_size)

print(f"Data count: {database.size().getInfo()}; Batch Count: {total_batches}")

for batch_num in range(total_batches):

    start_idx = batch_num * batch_size
    end_idx = min((batch_num + 1) * batch_size, database.size().getInfo())

    print(f"[Batch: {batch_num+1}; Range: {start_idx} - {end_idx}  Size: {(end_idx - start_idx)}]")


    batch_database = database.toList((end_idx - start_idx), start_idx)
    batch_database = ee.FeatureCollection(batch_database)

    df = batch_processing(image_list, batch_database, batch_num)
    merged_df = pd.concat([merged_df, df])
    
merged_df.to_csv(f"{year}_data.csv", index=False)
