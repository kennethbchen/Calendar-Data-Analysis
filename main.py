import matplotlib.dates
import matplotlib.pyplot as plt
import datetime
import json
import os.path
import numpy as np
import pandas as pd
import janitor

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

    #analysis_1(data, categories)

    #analysis_1a(data, categories)

    analysis_2(data, categories)


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

def analysis_1a(data, categories):

    print("Analysis 1a:")

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    data = data[data["startTime"].dt.year == 2023]
    print(data)
    counts = pd.DataFrame(0, index=day_names, columns=list(categories.keys()))

    for category in categories.keys():
        for i, day in enumerate(day_names):
            pass
            # Get only the events that match this category and day of week. The length of the query is the frequency
            freq = len(data[["summary"]].loc[data["summary"] == category].loc[data["startTime"].dt.dayofweek == i])
            counts.at[day, category] = freq

    print(counts)

    # Choose some categories to display
    counts = counts[["Sleep", "School", "Art", "Programming", "Game Dev", "3D Modeling"]].transpose()

    # Plot
    fig, ax = plt.subplots(len(counts.index), figsize=(8.5, 4))
    fig.subplots_adjust(hspace=0.2)

    fig.suptitle("Distribution of Event Categories by Day of Week")
    for i, label in enumerate(counts.index):

        ax[i].tick_params(labelleft=False, left=False)

        # Only label the bottommost subplot
        if i == len(counts.index) - 1:
            ax[i].set_xticks(range(len(day_names)), labels=day_names)
            ax[i].set_xlabel("Day of Week")
        else:
            ax[i].tick_params(labelbottom=False, bottom=False)

        ax[i].set_ylabel(label, loc="top", rotation=0)
        ax[i].yaxis.set_label_coords(x=-0.01, y=0.2)

        ax[i].bar(day_names, counts.loc[label])

    plt.show()
    #plt.savefig("figures/analysis_1a.png")

def analysis_2(data, categories):

    print("Analysis 2:")

    chosen_categories = ["Sleep", "School", "Art", "Programming", "Game Dev", "3D Modeling"]


    # Compute Running Average
    data = data.loc[(data["summary"] == "School") & (data["startTime"].dt.year == 2023), ["startTime", "delta_seconds"]].copy()

    data["date"] = data.loc[:, "startTime"].dt.date

    # Combine events that take place on the same day into one row
    data = data.loc[:, ["date", "delta_seconds"]].groupby("date").sum()

    # Fill in missing days as 0 delta_seconds
    data = data.asfreq("D", fill_value=0)

    data["delta_hours"] = data["delta_seconds"] / (60 * 60)

    data["cumulative_delta_hours"] = data["delta_hours"].rolling(window=14, min_periods=1).mean()

    with pd.option_context("display.max_rows", None):
        print(data)

    fig, ax = plt.subplots()
    fig.suptitle("Cumulative Mean of Duration of Events in the 'School' Category in 2023")

    ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator())
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%b'))

    ax.yaxis.grid()
    ax.set_ylabel("Event Duration (Hours)")

    ax.plot(data.index, data["cumulative_delta_hours"])

    plt.savefig("figures/analysis_2.png")


if __name__ == "__main__":
    main()