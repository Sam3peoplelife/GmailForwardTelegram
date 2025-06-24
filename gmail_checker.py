import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_auth_url(user_id):
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    auth_url, _ = flow.authorization_url(prompt='consent')
    # Store flow for this user if you want to support web callback
    return auth_url

def exchange_code_for_token(code, user_id):
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    flow.fetch_token(code=code)
    creds = flow.credentials
    # Return as dict for serialization
    return json.loads(creds.to_json())

def check_new_emails(token_dict, last_checked_id=None):
    creds = Credentials.from_authorized_user_info(token_dict, SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=10).execute()
    messages = results.get('messages', [])
    new_emails = []
    new_last_id = last_checked_id
    if not messages:
        return new_emails, last_checked_id
    for message in messages:
        msg_id = message['id']
        if last_checked_id is None or msg_id > last_checked_id:
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            headers = msg['payload']['headers']
            sender = next((header['value'] for header in headers if header['name'] == 'From'), '')
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), '')
            new_emails.append({'sender': sender, 'subject': subject})
            if new_last_id is None or msg_id > new_last_id:
                new_last_id = msg_id
    return new_emails, new_last_id