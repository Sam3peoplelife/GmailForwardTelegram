import os
import time
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Settings for Gmail API access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
LAST_CHECKED_ID = None
FIRST_RUN = True

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
    """Check for new messages in Gmail."""
    global LAST_CHECKED_ID
    global FIRST_RUN
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    
    # Get list of messages
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=10).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("No new messages.")
        return
    
    # Check for new messages
    for message in messages:
        if FIRST_RUN:
            FIRST_RUN = False
            break
        msg_id = message['id']
        if LAST_CHECKED_ID is None or msg_id > LAST_CHECKED_ID:
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            headers = msg['payload']['headers']
            sender = next(header['value'] for header in headers if header['name'] == 'From')
            subject = next(header['value'] for header in headers if header['name'] == 'Subject')
            print(f"New message from: {sender}")
            print(f"Subject: {subject}")
            print("-" * 50)
    
    # Update last checked ID
    if messages:
        LAST_CHECKED_ID = messages[0]['id']

def main():
    """Main function for periodic checking."""
    print("Starting Gmail check every 5 minutes...")
    while True:
        try:
            check_new_emails()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)  # 5 minutes in seconds

if __name__ == '__main__':
    main()