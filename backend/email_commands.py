from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
import logging
import base64

class EmailCommandHandler:
    def __init__(self):
        self.current_tab = "INBOX"
        self.current_index = 0
        self.current_email_id = None
        self.gmail_service = None
        self.credentials = None
        self.emails_cache = []
        self.search_query = None  # Add state for search query
        
    def initialize(self, credentials_json: str):
        """Initialize the Gmail service with credentials"""
        try:
            self.credentials = Credentials.from_authorized_user_info(json.loads(credentials_json))
            self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
            return True
        except Exception as e:
            logging.error(f"Failed to initialize Gmail service: {str(e)}")
            return False

    def get_email_content(self, email_id: str) -> Dict[str, Any]:
        """Get email content by ID"""
        try:
            message = self.gmail_service.users().messages().get(
                userId='me', 
                id=email_id, 
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            
            # Get email body
            body = ""
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
            else:
                data = message['payload']['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
            
            return {
                'id': email_id,
                'subject': subject,
                'sender': sender,
                'body': body,
                'labels': message['labelIds']
            }
        except Exception as e:
            logging.error(f"Error getting email content: {str(e)}")
            return None

    def read_email_body(self) -> str:
        """Read the full body of the current email"""
        if not self.current_email_id:
            return "No email selected"
        
        email = self.get_email_content(self.current_email_id)
        if email:
            return f"Email from {email['sender']}. Subject: {email['subject']}. Message: {email['body']}"
        return "Could not read email content"

    def mark_as_unread(self) -> bool:
        """Mark the current email as unread"""
        if not self.current_email_id:
            return False
        
        try:
            self.gmail_service.users().messages().modify(
                userId='me',
                id=self.current_email_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            logging.error(f"Error marking email as unread: {str(e)}")
            return False

    def delete_email(self) -> bool:
        """Move the current email to trash"""
        if not self.current_email_id:
            return False
        
        try:
            self.gmail_service.users().messages().trash(
                userId='me',
                id=self.current_email_id
            ).execute()
            return True
        except Exception as e:
            logging.error(f"Error deleting email: {str(e)}")
            return False

    def star_email(self) -> bool:
        """Mark the current email as important/starred"""
        if not self.current_email_id:
            return False
        
        try:
            self.gmail_service.users().messages().modify(
                userId='me',
                id=self.current_email_id,
                body={'addLabelIds': ['STARRED']}
            ).execute()
            return True
        except Exception as e:
            logging.error(f"Error starring email: {str(e)}")
            return False

    def archive_email(self) -> bool:
        """Archive the current email"""
        if not self.current_email_id:
            return False
        
        try:
            self.gmail_service.users().messages().modify(
                userId='me',
                id=self.current_email_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            return True
        except Exception as e:
            logging.error(f"Error archiving email: {str(e)}")
            return False

    def unarchive_email(self) -> bool:
        """Unarchive the current email (move back to INBOX and untrash if needed)"""
        if not self.current_email_id:
            return False
        
        try:
            # First try to untrash it in case it was in Trash
            try:
                self.gmail_service.users().messages().untrash(
                    userId='me',
                    id=self.current_email_id
                ).execute()
            except Exception as e:
                # If it's not in Trash, this will fail, which is fine
                logging.debug(f"Email not in trash: {str(e)}")
            
            # Then add the INBOX label to ensure it's in the inbox
            self.gmail_service.users().messages().modify(
                userId='me',
                id=self.current_email_id,
                body={'addLabelIds': ['INBOX']}
            ).execute()
            return True
        except Exception as e:
            logging.error(f"Error unarchiving email: {str(e)}")
            return False




    def switch_tab(self, tab: str) -> bool:
        """Switch to a different email tab/category"""
        valid_tabs = ['INBOX', 'PROMOTIONS', 'SOCIAL', 'ARCHIVE', 'STARRED', 'IMPORTANT']
        if tab.upper() not in valid_tabs:
            return False
        
        self.current_tab = tab.upper()
        self.current_index = 0
        self.emails_cache = []
        self.search_query = None  # Clear search when switching tabs
        return True

    def count_remaining_emails(self) -> int:
        """Count remaining unread emails in current tab"""
        try:
            if self.current_tab == 'ARCHIVE':
                query = '-label:INBOX is:unread'
            elif self.current_tab == 'STARRED':
                query = 'label:starred is:unread'
            elif self.current_tab == 'IMPORTANT':
                query = 'label:important is:unread'
            else:
                query = f'label:{self.current_tab} is:unread'
                
            response = self.gmail_service.users().messages().list(
                userId='me',
                q=query
            ).execute()
            
            return len(response.get('messages', []))
        except Exception as e:
            logging.error(f"Error counting unread emails: {str(e)}")
            return 0

    def count_total_emails(self) -> int:
        """Count total emails in current tab/view"""
        try:
            if self.current_tab == 'ARCHIVE':
                query = '-label:INBOX -label:TRASH -label:SPAM'
            elif self.current_tab == 'STARRED':
                query = 'label:starred'
            elif self.current_tab == 'IMPORTANT':
                query = 'label:important'
            else:
                query = f'label:{self.current_tab}'
            
            response = self.gmail_service.users().messages().list(
                userId='me',
                q=query
            ).execute()
            
            return len(response.get('messages', []))
        except Exception as e:
            logging.error(f"Error counting total emails: {str(e)}")
            return 0

    def search_emails(self, keyword: str) -> list:
        """Search emails with the given keyword"""
        try:
            self.search_query = keyword  # Store the search query
            # We don't need to return the content of the first email here anymore for the list view,
            # but interpret_command might want it. For now, let's keep it consistent or rely on fetch_emails.
            # Actually, let's just update the state here. The fetch_emails loop will handle the display.
            # But the original code returned the first email content to read it out?
            # "read it accessing the list" -> interpret_command uses the return value.
            
            return self._perform_search(keyword)
        except Exception as e:
            logging.error(f"Error searching emails: {str(e)}")
            return None

    def _perform_search(self, keyword: str):
        query = f'{keyword}' # Search globally or within tab? Original was label:current_tab. Let's stick to global or just keyword which implies all mail usually.
        # Original: query = f'label:{self.current_tab} {keyword}'
        # If I am searching I probably want to search everything?
        # User said "search for particular email name".
        # Let's allow global search for better UX, or stick to current tab if safer. 
        # The prompt implies "search for specific email", usually implies searching 'all'.
        # Let's use `label:{self.current_tab} {keyword}` to minimize change scope, OR just `{keyword}`.
        # Let's stick to the previous logic but persist it.
        query = f'label:{self.current_tab} {keyword}'
        
        response = self.gmail_service.users().messages().list(
            userId='me',
            q=query
        ).execute()
        
        messages = response.get('messages', [])
        self.emails_cache = messages
        self.current_index = 0
        
        if messages:
            self.current_email_id = messages[0]['id']
            return self.get_email_content(self.current_email_id)
        return None

    def fetch_emails(self) -> Dict[str, Any]:
        """Fetch emails based on current state (Search or Tab)"""
        try:
            messages = []
            speech_text = ""
            
            if self.search_query:
                # Active search
                query = f'label:{self.current_tab} {self.search_query}'
                speech_text = f"Found emails for {self.search_query}. "
            else:
                # Normal listing
                if self.current_tab == 'ARCHIVE':
                     query = '-label:INBOX -label:TRASH -label:SPAM' # Show archived emails
                     speech_text = "Here is the list of archive emails. "
                elif self.current_tab == 'STARRED':
                     query = 'label:STARRED'
                     speech_text = "Here is the list of starred emails. "
                elif self.current_tab == 'IMPORTANT':
                     query = 'label:important'
                     speech_text = "Here is the list of {{count}} important emails. "
                else:
                    query = f'label:{self.current_tab}'
                    speech_text = f"You have {{count}} emails in your {self.current_tab.lower()}. "
            
            logging.info(f"Fetching emails with query: {query}")
            
            # Execute query
            response = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()
            
            messages = response.get('messages', [])
            print(f"DEBUG: Found {len(messages)} messages for query '{query}'")
            
            # Update speech text count
            if not self.search_query and "{count}" in speech_text: # Only replace if placeholder exists
                speech_text = speech_text.replace("{count}", str(len(messages)))
            elif len(messages) == 0 and not self.search_query and "list of archive" not in speech_text:
                 # If empty and not archive (which has its own text), say something? 
                 # Actually the original logic was: if search_query and 0 results -> "No emails found...".
                 # If normal list and 0 results -> "You have 0 emails..." (handled by replace).
                 pass
            elif len(messages) == 0 and self.search_query:
                speech_text = f"No emails found for {self.search_query}."
                
            emails = []
            for msg in messages:
                email = self.get_email_content(msg['id'])
                if email:
                    emails.append(email)
                    if 'UNREAD' in email['labels'] and not self.search_query: # Only announce unread details in normal view effectively? Or both?
                        # User complaint: "reading all emails... instead of reading specific email"
                        # If search found results, we probably only want to list them visually and maybe say "Found X emails".
                        # If the user asks to "read", that's a separate command.
                        # The app.py logic was: "Unread email from X...".
                        # If I searched, I probably want to hear about the search results.
                        speech_text += f"Email from {email['sender']}, subject: {email['subject']}. "
            
            return {
                "emails": emails,
                "speech_response": speech_text
            }
        except Exception as e:
            logging.error(f"Error fetching emails: {str(e)}")
            raise e

    def interpret_command(self, command_text: str) -> Dict[str, Any]:
        """Interpret and execute voice commands"""
        command_text = command_text.lower().replace("e-mail", "email")
        response = {
            'action': None,
            'message': None,
            'success': True
        }

        try:
            if "read email" in command_text:
                try:
                    name = command_text.split("read email")[-1].strip()
                    if name:
                        # Search for email to read
                        search_results = self._perform_search(name)
                        if search_results and self.current_email_id:
                            email_data = search_results
                            body_content = self.read_email_body()
                            response['message'] = body_content
                            response['action'] = 'read'
                            response['email'] = email_data
                        else:
                            response['message'] = f"Could not find email from {name}"
                            response['success'] = False
                    else:
                        # Read current
                        if self.current_email_id:
                             response['message'] = self.read_email_body()
                             response['action'] = 'read'
                             response['email'] = self.get_email_content(self.current_email_id)
                        else:
                             response['message'] = "No email selected to read"
                             response['success'] = False
                except Exception as e:
                    logging.error(f"Error in read email command: {str(e)}")
                    response['message'] = "Error reading email"
                    response['success'] = False

            elif "read body" in command_text or "read full" in command_text:
                response['message'] = self.read_email_body()
                response['action'] = 'read'
            
            elif "mark as unread email" in command_text:
                try:
                    name = command_text.split("mark as unread email")[-1].strip()
                    if name:
                        # Search for email to mark unread
                        search_results = self._perform_search(name)
                        if search_results and self.current_email_id:
                            email_data = search_results
                            success = self.mark_as_unread()
                            if success:
                                response['message'] = f"Marked email from {search_results['sender']} as unread"
                                response['action'] = 'mark_unread'
                                response['email'] = email_data
                            else:
                                response['message'] = "Failed to mark email as unread"
                                response['success'] = False
                        else:
                            response['message'] = f"Could not find email from {name}"
                            response['success'] = False
                    else:
                        # Mark current as unread
                        if self.current_email_id:
                             email_data = self.get_email_content(self.current_email_id)
                             success = self.mark_as_unread()
                             response['message'] = "Email marked as unread" if success else "Failed to mark email as unread"
                             response['action'] = 'mark_unread'
                             if success:
                                 response['email'] = email_data
                        else:
                             response['message'] = "No email selected"
                             response['success'] = False
                except Exception as e:
                    logging.error(f"Error in mark unread email command: {str(e)}")
                    response['message'] = "Error marking email as unread"
                    response['success'] = False

            elif "mark as unread" in command_text:
                success = self.mark_as_unread()
                response['message'] = "Email marked as unread" if success else "Failed to mark email as unread"
                response['action'] = 'mark_unread'
            
            
            elif ("show" in command_text or "give" in command_text or "list" in command_text) and "important" in command_text:
                self.current_tab = "INBOX" # Reset to inbox or search globally?
                result = self.search_emails("is:starred")
                response['message'] = "Showing important emails" if result else "No important emails found"
                response['action'] = 'search'

            elif "mark email" in command_text and "starred" in command_text:
                try:
                    # Look for name between "mark email" and "as starred" or just "mark email [name] as starred"
                    # Pattern: "mark email [name] as starred"
                    name_part = command_text.split("mark email")[-1].split("as starred")[0].strip()
                    if name_part:
                        search_results = self._perform_search(name_part)
                        if search_results and self.current_email_id:
                            email_data = search_results
                            success = self.star_email()
                            if success:
                                response['message'] = f"Marked email from {search_results['sender']} as starred"
                                response['action'] = 'star'
                                response['email'] = email_data
                            else:
                                response['message'] = "Failed to star email"
                                response['success'] = False
                        else:
                            response['message'] = f"Could not find email from {name_part}"
                            response['success'] = False
                    else:
                        response['message'] = "Please specify the email name"
                        response['success'] = False
                except Exception as e:
                    logging.error(f"Error in star by name command: {str(e)}")
                    response['message'] = "Error starring email"
                    response['success'] = False

            elif "important" in command_text or "star" in command_text:
                success = self.star_email()
                response['message'] = "Email starred" if success else "Failed to star email"
                response['action'] = 'star'

            elif "delete email" in command_text:
                try:
                    name = command_text.split("delete email")[-1].strip()
                    if name:
                        # Search for email to delete
                        search_results = self._perform_search(name)
                        if search_results and self.current_email_id:
                            email_data = search_results
                            success = self.delete_email()
                            if success:
                                response['message'] = f"Deleted email from {search_results['sender']}"
                                response['action'] = 'delete'
                                response['email'] = email_data
                            else:
                                response['message'] = "Failed to delete email"
                                response['success'] = False
                        else:
                            response['message'] = f"Could not find email from {name}"
                            response['success'] = False
                    else:
                        # Delete current
                        if self.current_email_id:
                             email_data = self.get_email_content(self.current_email_id)
                             success = self.delete_email()
                             response['message'] = "Email deleted" if success else "Failed to delete email"
                             response['action'] = 'delete'
                             if success:
                                 response['email'] = email_data
                        else:
                             response['message'] = "No email selected to delete"
                             response['success'] = False
                except Exception as e:
                    logging.error(f"Error in delete email command: {str(e)}")
                    response['message'] = "Error deleting email"
                    response['success'] = False

            elif "delete" in command_text: # Generic delete for currently selected email
                if self.current_email_id:
                    email_data = self.get_email_content(self.current_email_id)
                    success = self.delete_email()
                    response['message'] = "Email deleted" if success else "Failed to delete email"
                    response['action'] = 'delete'
                    if success:
                        response['email'] = email_data
                else:
                    response['message'] = "No email selected to delete"
                    response['success'] = False

            elif "unarchive email" in command_text:
                try:
                    name = command_text.split("unarchive email")[-1].strip()
                    if name:
                        query = f'{name} -label:INBOX' # Search specifically for archived items
                        results = self.gmail_service.users().messages().list(userId='me', q=query).execute()
                        messages = results.get('messages', [])
                        
                        if messages:
                            # Found archived email
                            self.current_email_id = messages[0]['id']
                            email_data = self.get_email_content(self.current_email_id)
                            
                            success = self.unarchive_email()
                            if success:
                                response['message'] = f"Unarchived email from {email_data['sender']}"
                                response['action'] = 'archive' 
                                response['email'] = email_data 
                            else:
                                response['message'] = "Failed to unarchive email"
                                response['success'] = False
                        else:
                            response['message'] = "Not archived"
                            response['success'] = False
                    else:
                        # Unarchive current email
                         if self.current_email_id:
                             success = self.unarchive_email()
                             response['message'] = "Email unarchived" if success else "Failed to unarchive"
                             response['action'] = 'archive'
                         else:
                             response['message'] = "No email selected to unarchive"
                             response['success'] = False

                except Exception as e:
                    logging.error(f"Error in unarchive command: {str(e)}")
                    response['message'] = "Error unarchiving email"
                    response['success'] = False
            
            elif "archive email" in command_text:
                # Handle "archive email [name]"
                try:
                    name = command_text.split("archive email")[-1].strip()
                    if name:
                        # Search for the email first
                        search_results = self._perform_search(name)
                        if search_results and self.current_email_id:
                           # Store email data before archiving (to return to UI)
                           email_data = search_results 
                           # Archive the found email
                           success = self.archive_email()
                           response['message'] = f"Archived email from {search_results['sender']}" if success else "Failed to archive email"
                           response['action'] = 'archive'
                           if success:
                               response['email'] = email_data # Return email for UI to remove
                        else:
                            response['message'] = f"Could not find email from {name}"
                            response['success'] = False
                    else:
                        # Fallback to current
                        if self.current_email_id:
                            email_data = self.get_email_content(self.current_email_id)
                            success = self.archive_email()
                            response['message'] = "Email archived" if success else "Failed to archive email"
                            response['action'] = 'archive'
                            if success:
                                response['email'] = email_data
                        else:
                             response['message'] = "No email selected to archive"
                             response['success'] = False
                except Exception as e:
                     logging.error(f"Error in archive email command: {e}")
                     response['message'] = "Error archiving email"
                     response['success'] = False

            elif "switch to archive" in command_text or "go to archive" in command_text:
                success = self.switch_tab("ARCHIVE")
                response['message'] = "Switched to archive" if success else "Failed to switch to archive"
                response['action'] = 'switch_tab'

            elif "switch to starred" in command_text or "go to starred" in command_text:
                success = self.switch_tab("STARRED")
                response['message'] = "Switched to starred" if success else "Failed to switch to starred"
                response['action'] = 'switch_tab'

            elif "important" in command_text and ("switch" in command_text or "go to" in command_text or "show" in command_text):
                success = self.switch_tab("IMPORTANT")
                response['message'] = "Switched to important" if success else "Failed to switch to important"
                response['action'] = 'switch_tab'

            elif "archive" in command_text and "unarchive" not in command_text: # Fallback for simple "archive" command
                if self.current_email_id:
                     email_data = self.get_email_content(self.current_email_id)
                     success = self.archive_email()
                     response['message'] = "Email archived" if success else "Failed to archive email"
                     response['action'] = 'archive'
                     if success:
                         response['email'] = email_data
                else:
                     response['message'] = "No email selected to archive"
                     response['success'] = False
            
            elif command_text in ["go on", "next", "continue"]:
                response['action'] = 'next'
            
            elif "previous" in command_text or "go back" in command_text:
                response['action'] = 'previous'
            
            elif "stop reading" in command_text:
                response['action'] = 'stop'
            
            elif "start reading" in command_text or "resume reading" in command_text:
                response['action'] = 'start'
            
            elif "promotions" in command_text:
                success = self.switch_tab("PROMOTIONS")
                response['message'] = "Switched to promotions" if success else "Failed to switch tab"
                response['action'] = 'switch_tab'
            
            elif "social" in command_text:
                success = self.switch_tab("SOCIAL")
                response['message'] = "Switched to social" if success else "Failed to switch tab"
                response['action'] = 'switch_tab'
            
            elif "inbox" in command_text:
                success = self.switch_tab("INBOX")
                response['message'] = "Switched to inbox" if success else "Failed to switch tab"
                response['action'] = 'switch_tab'
            
            elif "how many" in command_text:
                count = self.count_remaining_emails()
                response['message'] = f"You have {count} unread emails in {self.current_tab.lower()}"
                response['action'] = 'count'

            elif "count" in command_text and "email" in command_text:
                count = self.count_total_emails()
                response['message'] = f"You have a total of {count} emails in your {self.current_tab.lower()}"
                response['action'] = 'count'
            
            elif "start from beginning" in command_text:
                self.current_index = 0
                self.search_query = None # Reset search
                response['action'] = 'reset'
                response['message'] = "Starting from the beginning"
            
            elif "search for" in command_text:
                keyword = command_text.split("search for")[-1].strip()
                result = self.search_emails(keyword)
                response['message'] = f"Found emails matching '{keyword}'" if result else f"No emails found matching '{keyword}'"
                response['action'] = 'search'
            
            else:
                response['message'] = "Sorry, I didn't understand that command"
                response['success'] = False

        except Exception as e:
            logging.error(f"Error processing command: {str(e)}")
            response['message'] = "An error occurred while processing your command"
            response['success'] = False

        # Ensure speech_response is set if not already
        if 'speech_response' not in response:
            response['speech_response'] = response.get('message', '')

        return response

# Create a singleton instance
email_commander = EmailCommandHandler() 