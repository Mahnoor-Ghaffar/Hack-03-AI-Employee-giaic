"""
Gmail Email Sender - Production Implementation

Sends real emails via Gmail API using OAuth2 authentication.
Handles token refresh automatically and stores token.pickle for reuse.

Usage:
    python scripts/send_email.py --to recipient@example.com --subject "Test" --body "Hello"

Requirements:
    - Gmail API enabled in Google Cloud Console
    - OAuth2 credentials (client_secret.json or gmail_credentials.json)
    - First run triggers OAuth consent screen and creates token.pickle
"""

import sys
import os
import base64
import pickle
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Gmail API imports
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration - resolved relative to this script's location (not current working directory)
BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = BASE_DIR / "gmail_credentials.json"
CLIENT_SECRET_FILE = BASE_DIR / "client_secret.json"
TOKEN_FILE = BASE_DIR / "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Paths
VAULT_PATH = BASE_DIR / "AI_Employee_Vault"
ACTION_LOG_PATH = VAULT_PATH / "Logs" / "actions.log"

# Ensure log directory exists
ACTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def log_action(message: str, level: str = "INFO"):
    """Log action to actions.log file."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] [{level}] {message}\n"

    with open(ACTION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)


def get_credentials() -> Optional[Credentials]:
    """
    Obtain Gmail API credentials via OAuth2 flow.
    
    First run: Opens browser for OAuth consent, saves token.pickle
    Subsequent runs: Loads and refreshes token.pickle automatically
    
    Returns:
        Credentials object or None if authentication fails
    """
    creds = None

    # Load existing token
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)
            log_action("Loaded existing Gmail token from token.pickle")
        except Exception as e:
            log_action(f"Failed to load token.pickle: {e}", "ERROR")
            TOKEN_FILE.unlink(missing_ok=True)
            creds = None

    # Refresh or obtain new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                log_action("Gmail credentials refreshed successfully")
            except Exception as e:
                log_action(f"Token refresh failed: {e}", "ERROR")
                creds = None

        if not creds or not creds.valid:
            # Find client secrets file
            secrets_file = None
            if CLIENT_SECRET_FILE.exists():
                secrets_file = CLIENT_SECRET_FILE
            elif CREDENTIALS_FILE.exists():
                # Check if gmail_credentials.json has client_secret format
                try:
                    with open(CREDENTIALS_FILE, "r") as f:
                        cred_data = json.load(f)
                    # If it's an authorized_user type, we need the original client_secret.json
                    if cred_data.get("type") == "authorized_user":
                        log_action("Existing credentials found but invalid, need client_secret.json for re-auth", "WARNING")
                except:
                    pass
            
            if not secrets_file:
                log_action("No client_secret.json found for OAuth flow", "ERROR")
                return None

            # Run OAuth flow
            try:
                log_action("Starting OAuth2 authorization flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    secrets_file, SCOPES
                )
                creds = flow.run_local_server(port=0)
                
                if creds:
                    # Save token for future use
                    with open(TOKEN_FILE, "wb") as token:
                        pickle.dump(creds, token)
                    log_action("OAuth2 completed, token.pickle saved")
                    
            except Exception as e:
                log_action(f"OAuth2 flow failed: {e}", "ERROR")
                return None

    return creds


def get_gmail_service() -> Optional[Any]:
    """
    Build Gmail API service with OAuth2 credentials.

    Returns:
        Gmail API service object or None if authentication fails
    """
    try:
        creds = get_credentials()

        if not creds:
            log_action("Gmail authentication failed", "ERROR")
            return None

        service = build("gmail", "v1", credentials=creds)
        log_action("Gmail API service initialized successfully")
        return service

    except Exception as e:
        log_action(f"Failed to initialize Gmail API service: {e}", "ERROR")
        return None


def create_message(to: str, subject: str, body: str, html: bool = False) -> MIMEText:
    """
    Create email message.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        html: If True, treat body as HTML

    Returns:
        MIMEText message object
    """
    message = MIMEMultipart("alternative")
    message["to"] = to
    message["subject"] = subject

    # Add plain text or HTML version
    text_part = MIMEText(body, "plain" if not html else "html", "utf-8")
    message.attach(text_part)

    return message


def send_gmail_email(to: str, subject: str, body: str, html: bool = False) -> Dict[str, Any]:
    """
    Send email via Gmail API.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        html: If True, send as HTML email

    Returns:
        Dictionary with status and message
    """
    try:
        service = get_gmail_service()

        if not service:
            return {
                "status": "error",
                "message": "Failed to initialize Gmail API service"
            }

        # Create and encode email message
        message = create_message(to, subject, body, html)
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        # Send via Gmail API
        sent_message = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw_message})
            .execute()
        )

        message_id = sent_message.get("id", "unknown")
        log_action(f"Gmail email sent successfully to {to} (Message ID: {message_id})")

        return {
            "status": "success",
            "message": f"Email sent to {to}",
            "message_id": message_id
        }

    except HttpError as error:
        error_details = error.content.decode("utf-8") if error.content else str(error)
        log_action(f"Gmail API error: {error_details}", "ERROR")
        return {
            "status": "error",
            "message": f"Gmail API error: {error_details}"
        }

    except Exception as e:
        log_action(f"Failed to send Gmail email: {e}", "ERROR")
        return {
            "status": "error",
            "message": f"Failed to send email: {e}"
        }


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Send email via Gmail API"
    )
    parser.add_argument(
        "--to",
        required=True,
        help="Recipient email address"
    )
    parser.add_argument(
        "--subject",
        required=True,
        help="Email subject"
    )
    parser.add_argument(
        "--body",
        required=True,
        help="Email body content"
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Send as HTML email"
    )

    args = parser.parse_args()

    result = send_gmail_email(
        to=args.to,
        subject=args.subject,
        body=args.body,
        html=args.html
    )

    # Clean output
    if result["status"] == "success":
        print(f"SUCCESS: {result['message']}")
        if result.get("message_id"):
            print(f"Message ID: {result['message_id']}")
    else:
        print(f"ERROR: {result['message']}")

    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()
