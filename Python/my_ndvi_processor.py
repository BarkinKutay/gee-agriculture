import ee
import pandas as pd
import math

class NDVIProcessor:
    def __init__(self, project_id, parcel_data_id, year, month_range, count, batch_size):
        self.project_id = project_id
        self.parcel_data_id = parcel_data_id
        self.year = year
        self.month_range = month_range
        self.count = count
        self.batch_size = batch_size
        self.image_data = None
        self.parsel_data = None

    def initialize(self):
        ee.Initialize(project=self.project_id)
        self.parsel_data = ee.FeatureCollection(self.parcel_data_id)
        self.image_data = ee.ImageCollection("COPERNICUS/S2")

    def add_ndvi(self, input_image):
        nd = input_image.normalizedDifference(["B8", "B4"]).rename("ndvi")
        return input_image.addBands(nd)

    def get_monthly_image_collection(self):
        image_collection = ee.ImageCollection([])

        for month in range(self.month_range):
            start_date = ee.Date.fromYMD(self.year, month + 1, 1)
            end_date = start_date.advance(1, "month")

            image = (
                self.image_data
                .filterDate(start_date, end_date)
                .map(self.add_ndvi)
                .median()
                .select("ndvi")
            )

            image = image.set("month", str(month))
            image_collection = image_collection.merge(ee.ImageCollection([image]))

        return image_collection

    def feature_collection_init(self, feature):
        tarimParse = feature.get("TarimParse")
        geometry = feature.geometry()
        return ee.Feature(geometry).set("TarimParse", tarimParse).set("mean_ndvi", [])

    def collect_data(self, image, database):
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

    def data_conversion(self, df):
        df["peak_month"] = df["mean_ndvi"].apply(lambda x: x.index(max(x)) + 1)
        df["peak_list"] = df["mean_ndvi"].apply(self.peak_list)
        df["peak_count"] = df["peak_list"].apply(lambda x: len(x))

    def peak_list(self, parsel_ndvi):
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

    def batch_processing(self, image_list, database, batch_num):
        data_list = []

        for month in range(image_list.size().getInfo()):
            image = ee.Image(image_list.get(month))
            database = self.collect_data(image, database)

        for feature in database.getInfo()["features"]:
            properties = feature["properties"]
            properties[".geo"] = feature["geometry"]
            data_list.append(properties)

        df = pd.DataFrame(data_list)
        self.data_conversion(df)

        column_to_move = df.pop(".geo")
        df.insert(len(df.columns), ".geo", column_to_move)
        return df

    def process_data(self):
        self.initialize()
        database = self.parsel_data.distinct("TarimParse").limit(self.count).map(self.feature_collection_init)

        image_collection = self.get_monthly_image_collection()
        image_list = image_collection.toList(self.month_range)

        merged_df = pd.DataFrame()

        total_batches = math.ceil(database.size().getInfo() / self.batch_size)

        print(f"Data count: {database.size().getInfo()}; Batch Count: {total_batches}")

        for batch_num in range(total_batches):
            start_idx = batch_num * self.batch_size
            end_idx = min((batch_num + 1) * self.batch_size, database.size().getInfo())

            print(f"[Batch: {batch_num+1}; Range: ({start_idx} - {end_idx}); Size: {(end_idx - start_idx)}] : ", end="")

            batch_database = database.toList((end_idx - start_idx), start_idx)
            batch_database = ee.FeatureCollection(batch_database)

            df = self.batch_processing(image_list, batch_database, batch_num)
            merged_df = pd.concat([merged_df, df])

            print("Done")

        merged_df.to_csv(f"{self.year}_data.csv", index=False)

if __name__ == "__main__":
    ndvi_processor = NDVIProcessor(
        project_id="ee-bau-tubitak-ndvi",
        parcel_data_id="projects/ee-bau-tubitak-ndvi/assets/DestekParselleri",
        year=2018,
        month_range=12,
        count=980,
        batch_size=980
    )
    ndvi_processor.process_data()