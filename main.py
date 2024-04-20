
import datetime
import json
import os.path
import numpy as np
import pandas as pd

from functools import partial

from fetch_data import get_data

from thefuzz import fuzz

pd.options.display.width = 0
pd.options.display.float_format = '{:,.2f}'.format

def get_category(categories, index):

    # Compare index to list of aliases
    for i, (name, aliases) in enumerate(categories.items()):

        for alias in aliases:
            if fuzz.ratio(index, alias) > 80:
                # Match
                return name

    # No match, add as a new category
    categories[index] = [index]
    return index

def get_periods(df):
    return pd.period_range(df["startTime"], df["endTime"], freq="h")

def main():

    data = get_data(force_fetch_data=False)
    
    # Parse time strings into datetime objects
    data["startTime"] = pd.to_datetime(data["startTime"], utc=True)
    data["startTime"] = data["startTime"].dt.tz_convert("EST")

    data["endTime"] = pd.to_datetime(data["endTime"], utc=True)
    data["endTime"] = data["endTime"].dt.tz_convert("EST")


    # Preprocessing:
    # Convert summary to canonical name
    # Maps a canonical category name to a list of valid aliases of that name
    categories = {}

    if os.path.exists("config.json"):
        print("Loaded categories")
        categories = json.load(open("config.json"))["categories"]

    # make summary column match their canonical category
    data["summary"] = data["summary"].apply(partial(get_category, categories))

    # Analysis:

    analysis_1(data, categories)

def analysis_1(data, categories):

    print("Analysis 1:")

    # convert each start and end time to a periodIndex (A list of time periods)
    data["periods"] = data[["startTime", "endTime"]].apply(get_periods, axis=1)

    # Get the hours of day that each event takes place in
    data["hours"] = [per.hour for per in data["periods"]]

    # For each hour of the day, get a count of every event for that hour
    counts = pd.DataFrame(0, index=range(0, 24 + 1), columns=list(categories.keys()))

    for category in categories.keys():
        for hour in range(0, 24 + 1):
            with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                freq = len(data[["summary", "hours"]].loc[data["summary"] == category].loc[
                               data["hours"].apply(lambda x: hour in x), ["summary"]])
                counts.at[hour, category] = freq

    print(counts)


if __name__ == "__main__":
    main()