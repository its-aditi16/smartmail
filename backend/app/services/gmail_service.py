from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List, Optional
import os
import json
import base64
from email.mime.text import MIMEText
from datetime import datetime
from ..models.email import EmailList, EmailDetail, EmailResponse

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailService:
    def __init__(self):
        self.creds = self._get_credentials()
        self.service = build('gmail', 'v1', credentials=self.creds)

    def _get_credentials(self) -> Credentials:
        creds = None
        token_path = 'credentials/token.json'
        credentials_path = 'credentials/credentials.json'

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        return creds

    async def list_emails(self, label: str = "INBOX", page: int = 1, limit: int = 20) -> EmailList:
        try:
            start_index = (page - 1) * limit
            query = f"label:{label}"
            
            # Get total and unread counts
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=limit,
                pageToken=None if page == 1 else self._get_page_token(start_index)
            ).execute()

            messages = result.get('messages', [])
            total = result.get('resultSizeEstimate', 0)
            
            # Get unread count
            unread_result = self.service.users().messages().list(
                userId='me',
                q=f"label:{label} is:unread"
            ).execute()
            unread_count = unread_result.get('resultSizeEstimate', 0)

            emails = []
            for msg in messages:
                email = self.service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['Subject', 'From', 'Date']
                ).execute()

                headers = email['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

                emails.append(EmailResponse(
                    id=msg['id'],
                    subject=subject,
                    sender=sender,
                    date=date,
                    is_unread='UNREAD' in email['labelIds'],
                    snippet=email.get('snippet', '')
                ))

            return EmailList(
                emails=emails,
                total=total,
                unread_count=unread_count
            )

        except Exception as e:
            raise Exception(f"Error listing emails: {str(e)}")

    async def get_email(self, email_id: str) -> EmailDetail:
        try:
            email = self.service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()

            headers = email['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

            # Get the email body
            body = self._get_email_body(email['payload'])

            return EmailDetail(
                id=email_id,
                subject=subject,
                sender=sender,
                date=date,
                is_unread='UNREAD' in email['labelIds'],
                body=body,
                labels=email['labelIds']
            )

        except Exception as e:
            raise Exception(f"Error getting email: {str(e)}")

    def _get_email_body(self, payload) -> str:
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    return base64.urlsafe_b64decode(part['body']['data']).decode()
                elif part['mimeType'] == 'text/html':
                    return base64.urlsafe_b64decode(part['body']['data']).decode()
        elif 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode()
        return "No content available"

    async def mark_as_read(self, email_id: str):
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            raise Exception(f"Error marking email as read: {str(e)}")

    async def mark_as_unread(self, email_id: str):
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
        except Exception as e:
            raise Exception(f"Error marking email as unread: {str(e)}")

    async def archive_email(self, email_id: str):
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
        except Exception as e:
            raise Exception(f"Error archiving email: {str(e)}")

    def _get_page_token(self, start_index: int) -> Optional[str]:
        if start_index == 0:
            return None
        
        try:
            result = self.service.users().messages().list(
                userId='me',
                maxResults=start_index
            ).execute()
            return result.get('nextPageToken')
        except Exception:
            return None 