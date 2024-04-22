# CalendarStats

This is some data analysis done on one of my personal Google Calendar calendars.

The calendar is used for planning the day via loose time blocking.

## Dataset

The dataset is omitted for privacy, but this project will extract Google Calendar information given that you have a Google Cloud project with access to the Google Calendar API.

The dataset is a csv that contains Google Calendar events created from 11/03/2018 onward (Approximately 14,000 events).

Each row is a unique event in the calendar and has the following columns:

summary - The name of each event. It generally corresponds to the name of a category of activity (e.g. "School" refers to doing school-related work).

startTime - Start time of the event

endTime - End time of the event

timeZone - Timezone of the event

delta_seconds - The duration of the event (time between start and end) in seconds.

### Notes

The naming scheme of summaries is not perfectly consistent and includes misspellings that will need to be corrected.

The timezone is mostly the same across all events, but is different in others which means certain times need to be adjusted.

## Analysis
Each analysis is done on a subset of the categories in the dataset

### 1
![A figure showing a distribution of event categories by hour of day](figures/analysis_1.png)

### 2
![A figure showing the Cumulative Mean of Duration of Events in the 'School' Category in 2023](figures/analysis_2.png)

### 3
![A figure showing the Distribution of Calendar Event Duration by Category](figures/analysis_3.png)
