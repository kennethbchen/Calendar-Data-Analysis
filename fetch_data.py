
import datetime
import json
import os.path
import pandas as pd

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from pyrfc3339 import parse as rfc_parse

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Uses https://developers.google.com/calendar/api/quickstart/python as a base

def get_data(force_fetch_data=False):

    print("Fetching data...")

    if not os.path.exists("data.csv") or force_fetch_data:

        creds = auth()

        try:
            data = fetch(creds)
            data.to_csv("data.csv", index=False)

        except HttpError as error:
            print(f"An error occurred: {error}")

    print("Loading data")
    data = pd.read_csv("data.csv")

    return data

def auth():
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds

def fetch(creds):

    calendar_id = None
    if os.path.exists("config.json"):
        calendar_id = json.load(open("config.json"))["calendar_id"]

    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API

    events = []
    next_page_token = None
    while True:
        print("Fetching...")
        events_result = (
            service.events()
                .list(
                calendarId=calendar_id,
                timeMin=datetime.datetime(2018, 1, 1).isoformat() + "Z",
                timeMax=datetime.datetime.utcnow().isoformat() + "Z",
                maxResults=2500,
                pageToken=next_page_token,
                orderBy="startTime",
                singleEvents=True,
            ).execute()
        )

        events.extend(events_result.get("items", []))

        if "nextPageToken" in events_result:
            next_page_token = events_result["nextPageToken"]  # Still more events to get, make another request
        else:
            break


    data = pd.DataFrame.from_records(events, columns=["summary", "start", "end"])

    # Unpack start and end dicts into columns
    # Rename columns, so they are not duplicated
    # Drop this timeZone value because we will get it later
    data = pd.concat([data, pd.json_normalize(data["start"]).drop("timeZone", axis=1).rename(columns={"dateTime": "startTime"})], axis=1)
    data.drop("start", axis=1, inplace=True)

    data = pd.concat([data, pd.json_normalize(data["end"]).rename(columns={"dateTime": "endTime"})], axis=1)
    data.drop("end", axis=1, inplace=True)

    data["startTime"] = data["startTime"].apply(rfc_parse)
    data["endTime"] = data["endTime"].apply(rfc_parse)

    # Time between start and end
    data["delta_seconds"] = (data["endTime"] - data["startTime"]).apply(datetime.timedelta.total_seconds)

    return data