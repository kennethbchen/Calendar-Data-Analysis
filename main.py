
import matplotlib.pyplot as plt
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

    if not os.path.exists("analysis_1.csv"):
        # convert each start and end time to a periodIndex (A list of time periods)
        data["periods"] = data[["startTime", "endTime"]].apply(get_periods, axis=1)

        # Get the hours of day that each event takes place in
        data["hours"] = [per.hour for per in data["periods"]]

        counts = pd.DataFrame(0, index=range(0, 24), columns=list(categories.keys()))

        for category in categories.keys():
            for hour in range(0, 24):

                # Get only the events that match this category and hour of day. The length of the query is the frequency
                freq = len(data[["summary", "hours"]].loc[data["summary"] == category].loc[data["hours"].apply(lambda x: hour in x), ["summary"]])
                counts.at[hour, category] = freq

        counts.to_csv("analysis_1.csv")

    counts = pd.read_csv("analysis_1.csv", header=0)

    # Choose some categories to display
    counts = counts[["Sleep", "School", "Art", "Programming", "Game Dev", "3D Modeling"]].transpose()
    print(counts)

    # Plot
    fig, ax = plt.subplots(len(counts.index), figsize=(8.5, 4))
    fig.subplots_adjust(hspace=0.2)

    fig.suptitle("Distribution of Event Categories by Hour of Day")
    for i, label in enumerate(counts.index):

        ax[i].tick_params(labelleft=False, left=False)

        # Only label the bottommost subplot
        if i == len(counts.index) - 1:
            ax[i].set_xticks(range(24))
            ax[i].set_xlabel("Hour of Day")
        else:
            ax[i].tick_params(labelbottom=False, bottom=False)

        ax[i].set_ylabel(label, loc="top", rotation=0)
        ax[i].yaxis.set_label_coords(x=-0.01, y=0.2)

        ax[i].imshow(counts.loc[label].values.reshape(1, -1))

    plt.savefig("figures/analysis_1.png")

if __name__ == "__main__":
    main()