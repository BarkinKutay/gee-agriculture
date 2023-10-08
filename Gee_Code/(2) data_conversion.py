import pandas as pd
import os

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

def data_conversion(df):
    df["mean_ndvi"] = df["mean_ndvi"].apply(lambda x: x.strip("][").split(", "))
    df["peak_month"] = df["mean_ndvi"].apply(lambda x: x.index(max(x)) + 1)
    df["peak_list"] = df["mean_ndvi"].apply(Peak_List)
    df["peak_count"] = df["peak_list"].apply(lambda x: len(x))

def main():
    current_directory = os.getcwd()

    data_folder = os.path.join(current_directory, "Data")
    print(data_folder)
    if os.path.exists(data_folder):
        data_file_path = os.path.join(data_folder, "data.csv")

        df = pd.read_csv(data_file_path)

        data_conversion(df)
        print(df.head())

        df.pop("system:index")
        column_to_move = df.pop(".geo")
        df.insert(len(df.columns), ".geo", column_to_move)

        df.to_csv("assets_Data.csv", index=False)
    else:
        print("Please Import the data")

if __name__ == "__main__":
    main()
