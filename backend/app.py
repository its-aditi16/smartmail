from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from agent import start_agent, process_voice_command
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
import os
import json
import logging
import os
from email_commands import email_commander

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

app = FastAPI(title="Smartmail API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3005", "http://127.0.0.1:3005"],  # Allow React development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google OAuth configuration
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
REDIRECT_URI = "http://localhost:5000/auth/google/callback"

# Load client secrets
with open(CLIENT_SECRETS_FILE) as f:
    client_secrets = json.load(f)

class VoiceCommandRequest(BaseModel):
    command: str

class EmailResponse(BaseModel):
    message: str
    action: Optional[str] = None
    success: bool = True

class EmailItem(BaseModel):
    id: str
    subject: str
    sender: str
    date: str
    isUnread: bool

def get_gmail_service():
    if not os.path.exists('token.json'):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    with open('token.json', 'r') as token:
        creds = Credentials.from_authorized_user_info(json.load(token), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")
    
    return build('gmail', 'v1', credentials=creds)

@app.get("/")
async def root():
    return {"message": "Welcome to Smartmail API"}

@app.get("/api/emails")
async def get_emails():
    try:
        if not os.path.exists('token.json'):
            raise HTTPException(status_code=401, detail="Not authenticated")
            
        with open('token.json', 'r') as token:
            creds_json = token.read()
            
        # Initialize email commander if needed
        if not email_commander.gmail_service:
            if not email_commander.initialize(creds_json):
                raise HTTPException(status_code=500, detail="Failed to initialize email service")
        
        if not email_commander.gmail_service:
            if not email_commander.initialize(creds_json):
                raise HTTPException(status_code=500, detail="Failed to initialize email service")
        
        # Get emails for current state (Search or Tab) via commander
        return email_commander.fetch_emails()
        
    except Exception as e:
        logging.error(f"Error getting emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/google")
async def google_auth():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent screen to get refresh token
    )
    return RedirectResponse(authorization_url)

@app.get("/auth/google/callback")
async def google_auth_callback(code: str, state: str):
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        
        # Exchange code for credentials
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Verify we got a refresh token
        if not credentials.refresh_token:
            logging.error("No refresh token received in OAuth flow")
            return RedirectResponse(
                "http://localhost:3005?auth=error&message=No refresh token received. Please revoke access and try again."
            )
        
        # Store credentials securely
        try:
            with open('token.json', 'w') as token:
                token.write(credentials.to_json())
            logging.info("Successfully stored OAuth credentials")
        except Exception as e:
            logging.error(f"Failed to store credentials: {str(e)}")
            return RedirectResponse(
                "http://localhost:3005?auth=error&message=Failed to store credentials"
            )
        
        # Test the credentials by making a simple API call
        try:
            service = build('gmail', 'v1', credentials=credentials)
            service.users().getProfile(userId='me').execute()
            logging.info("Successfully validated Gmail API access")
        except Exception as e:
            logging.error(f"Failed to validate Gmail API access: {str(e)}")
            return RedirectResponse(
                "http://localhost:3005?auth=error&message=Failed to validate Gmail API access"
            )
        
        return RedirectResponse("http://localhost:3005?auth=success")
    except Exception as e:
        logging.error(f"OAuth callback error: {str(e)}")
        return RedirectResponse(
            f"http://localhost:3005?auth=error&message={str(e)}"
        )

@app.post("/api/voice/process")
async def handle_voice_command(request: VoiceCommandRequest):
    try:
        # Validate credentials and get service (handling refresh if needed)
        service = get_gmail_service()
        
        # Update commander with fresh service
        email_commander.gmail_service = service
        # Also update credentials in commander if needed, though service is the most important
        # email_commander.credentials = service.credentials 
        
        # Process the command
        response = email_commander.interpret_command(request.command)
        return response
        
    except Exception as e:
        logging.error(f"Error processing voice command: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/start")
async def start_email_assistant():
    try:
        # First check if we have valid credentials
        if not os.path.exists('token.json'):
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Initialize Gmail service first
        service = get_gmail_service()
        if not service:
            raise HTTPException(status_code=500, detail="Failed to initialize Gmail service")
            
        # Initialize the email assistant
        # response = await start_agent()
        response = {
            "status": "success",
            "message": "Email assistant initialized successfully (MOCKED)",
            "speech_response": "Hello! I'm ready to help you with your emails."
        }
        if not response:
            raise HTTPException(status_code=500, detail="Failed to initialize email assistant")
            
        if response.get("status") == "error":
            raise HTTPException(status_code=500, detail=response.get("message", "Unknown error"))
            
        return response
    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error starting email assistant: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
@app.head("/api/health")
async def health_check():
    """Simple health check endpoint that accepts both GET and HEAD methods"""
    return {"status": "ok", "message": "Service is running"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True) 