import os
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def sync_database_to_google_drive(
    db_file
):

    service_account_info = json.loads(
        os.environ[
            "GOOGLE_SERVICE_ACCOUNT_JSON"
        ]
    )

    credentials = (
        service_account.Credentials
        .from_service_account_info(
            service_account_info,
            scopes=[
                "https://www.googleapis.com/auth/drive"
            ]
        )
    )

    service = build(
        "drive",
        "v3",
        credentials=credentials
    )

    file_id = os.environ[
        "GOOGLE_DRIVE_FILE_ID"
    ]

    media = MediaFileUpload(
        db_file,
        mimetype=(
            "application/x-sqlite3"
        ),
        resumable=False
    )

    service.files().update(
        fileId=file_id,
        media_body=media
    ).execute()

    return True
