from os import environ

from apiclient import discovery
from google.oauth2 import service_account


def get_data_from_sheet(spreadsheet_id, sheet_range):  # pragma: no cover
    credentials = service_account.Credentials.from_service_account_file(
        environ["GCP_CREDENTIALS_PATH"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = discovery.build("sheets", "v4", credentials=credentials)
    return (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=sheet_range,
        )
        .execute()
    )["values"]
