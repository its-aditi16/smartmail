from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
import email
from datetime import datetime, timedelta
import os
import pickle
import json

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """Get an authorized Gmail API service instance"""
    if not os.path.exists('token.json'):
        raise Exception("Not authenticated")
    
    with open('token.json', 'r') as token:
        creds = Credentials.from_authorized_user_info(json.load(token))
    
    return build('gmail', 'v1', credentials=creds)

def fetch_unread_emails(label="INBOX", date="today"):
    """Fetch unread emails from specified label and date"""
    service = get_gmail_service()
    
    # Build query
    query = "is:unread"
    if date == "today":
        today = datetime.now().strftime('%Y/%m/%d')
        query += f" after:{today}"
    elif date == "yesterday":
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
        today = datetime.now().strftime('%Y/%m/%d')
        query += f" after:{yesterday} before:{today}"
    
    try:
        results = service.users().messages().list(
            userId='me',
            labelIds=[label],
            q=query
        ).execute()
        
        return results.get('messages', [])
    except Exception as e:
        print(f"Error fetching emails: {str(e)}")
        return []

def read_subject_sender(email_id):
    """Get subject and sender of an email"""
    service = get_gmail_service()
    
    try:
        message = service.users().messages().get(userId='me', id=email_id).execute()
        headers = message['payload']['headers']
        
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        
        return f"From: {sender}\nSubject: {subject}"
    except Exception as e:
        print(f"Error reading email headers: {str(e)}")
        return "Error reading email"

def read_body(email_id):
    """Get the body of an email"""
    service = get_gmail_service()
    
    try:
        message = service.users().messages().get(userId='me', id=email_id, format='full').execute()
        
        if 'parts' in message['payload']:
            parts = message['payload']['parts']
            data = parts[0]['body'].get('data', '')
        else:
            data = message['payload']['body'].get('data', '')
        
        # TODO: Decode base64 data and clean up the text
        return "Email body placeholder"  # Replace with actual decoded body
    except Exception as e:
        print(f"Error reading email body: {str(e)}")
        return "Error reading email body"

def mark_as_unread(email_id):
    """Mark an email as unread"""
    service = get_gmail_service()
    
    try:
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        return True
    except Exception as e:
        print(f"Error marking email as unread: {str(e)}")
        return False

def mark_as_important(email_id):
    """Mark an email as important"""
    service = get_gmail_service()
    
    try:
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'addLabelIds': ['IMPORTANT']}
        ).execute()
        return True
    except Exception as e:
        print(f"Error marking email as important: {str(e)}")
        return False

def switch_label(email_id, label):
    """Move an email to a different label"""
    service = get_gmail_service()
    
    try:
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'addLabelIds': [label]}
        ).execute()
        return True
    except Exception as e:
        print(f"Error switching label: {str(e)}")
        return False

def get_yesterday_unreads():
    """Get unread emails from yesterday"""
    return fetch_unread_emails(date="yesterday") 