import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Settings for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
LAST_CHECKED_ID = None

def authenticate_gmail():
    """Authenticate for Gmail API."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def check_new_emails():
    """Check for new messages in Gmail. Returns a list of new messages."""
    global LAST_CHECKED_ID
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    
    # Get list of messages
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=10).execute()
    messages = results.get('messages', [])
    
    new_emails = []
    if not messages:
        return new_emails
    
    # Check for new messages
    for message in messages:
        msg_id = message['id']
        if LAST_CHECKED_ID is None or msg_id > LAST_CHECKED_ID:
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            headers = msg['payload']['headers']
            sender = next(header['value'] for header in headers if header['name'] == 'From')
            subject = next(header['value'] for header in headers if header['name'] == 'Subject')
            new_emails.append({'sender': sender, 'subject': subject})
    
    # Update the last checked ID
    if messages:
        LAST_CHECKED_ID = messages[0]['id']
    
    return new_emails