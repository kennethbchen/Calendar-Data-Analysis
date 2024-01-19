
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

pd.options.display.width = 0

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Uses https://developers.google.com/calendar/api/quickstart/python as a base

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = auth()

    try:
        request(creds)

    except HttpError as error:
        print(f"An error occurred: {error}")

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

def request(creds):

    calendar_id = None
    if os.path.exists("config.json"):
        calendar_id = json.load(open("config.json"))["calendar_id"]

    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API

    events = []
    next_page_token = None
    while True:
        print(next_page_token)
        events_result = (
            service.events()
                .list(
                calendarId=calendar_id,
                timeMin=datetime.datetime(2018, 1, 1).isoformat() + "Z",
                timeMax=datetime.datetime.utcnow().isoformat() + "Z",
                maxResults=10,
                pageToken=next_page_token,
                orderBy="startTime",
                singleEvents=True,
            ).execute()
        )

        events.extend(events_result.get("items", []))

        if "nextPageToken" in events_result:
            break
            next_page_token = events_result["nextPageToken"]  # Still more events to get, make another request
        else:
            break

    # data = pd.DataFrame(columns=["Name", "Start", "End", "Duration"])

    print(events[0])

    print("===========")

    print(events[-1])

    print(len(events))


    data = pd.DataFrame.from_records(events, columns=["summary", "start", "end"])

    # Unpack start and end dicts into columns
    # Rename columns, so they are not duplicated
    # Drop this timeZone value because we will get it later
    data = pd.concat([data, pd.json_normalize(data["start"]).drop("timeZone", axis=1).rename(columns={"dateTime": "startTime"})], axis=1)
    data.drop("start", axis=1, inplace=True)

    data = pd.concat([data, pd.json_normalize(data["end"]).rename(columns={"dateTime": "endTime"})], axis=1)
    data.drop("end", axis=1, inplace=True)

    print(rfc_parse(data.iloc[0]["endTime"]) - rfc_parse(data.iloc[0]["startTime"]))

    data["startTime"] = data["startTime"].apply(rfc_parse)
    data["endTime"] = data["endTime"].apply(rfc_parse)

    data["delta"] = data["endTime"] - data["startTime"]

    print(data)

    return

if __name__ == "__main__":
    main()