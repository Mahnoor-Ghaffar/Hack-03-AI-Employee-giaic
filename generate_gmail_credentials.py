"""
Generate Gmail OAuth credentials for sending emails.
This script opens a browser for authorization and saves credentials to gmail_credentials.json.

Scopes:
    - https://www.googleapis.com/auth/gmail.send (send emails)
    - https://www.googleapis.com/auth/gmail.readonly (read emails - for watcher)
"""

import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Configuration
CLIENT_SECRET_FILE = "client_secret_138657784066-pfitpc3nldj0p7g2hgfkgqff6gf9hd7b.apps.googleusercontent.com.json"
CREDENTIALS_FILE = "gmail_credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly"
]


def main():
    # Load client secret
    client_secret_path = Path(CLIENT_SECRET_FILE)
    if not client_secret_path.exists():
        print(f"Error: Client secret file not found: {CLIENT_SECRET_FILE}")
        return

    with open(client_secret_path, "r") as f:
        client_config = json.load(f)

    # Create OAuth flow
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri="http://localhost"
    )

    # Run authorization (opens browser)
    print("Opening browser for authorization...")
    print("Please sign in with your Google account and grant Gmail read access.")
    credentials = flow.run_local_server(port=0)

    # Build credentials JSON in the required format
    credentials_json = {
        "client_id": client_config["installed"]["client_id"],
        "client_secret": client_config["installed"]["client_secret"],
        "refresh_token": credentials.refresh_token,
        "type": "authorized_user"
    }

    # Save credentials
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(credentials_json, f, indent=2)

    print(f"\n✓ Success! Credentials saved to: {Path(CREDENTIALS_FILE).absolute()}")
    print(f"  - client_id: {credentials_json['client_id']}")
    print(f"  - client_secret: {credentials_json['client_secret'][:10]}...")
    print(f"  - refresh_token: {credentials_json['refresh_token'][:10]}...")
    print(f"  - type: {credentials_json['type']}")


if __name__ == "__main__":
    main()
