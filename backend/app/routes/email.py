from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from ..models.email import EmailList, EmailDetail, VoiceCommand, CommandResponse
from ..services.gmail_service import GmailService
from ..services.voice_service import process_voice_command

router = APIRouter()

@router.get("/emails", response_model=EmailList)
async def get_emails(
    label: str = Query("INBOX", description="Email label/category"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    Get a list of emails from the specified label.
    """
    try:
        gmail = GmailService()
        emails = await gmail.list_emails(label, page, limit)
        return emails
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/emails/{email_id}", response_model=EmailDetail)
async def get_email(email_id: str):
    """
    Get detailed information about a specific email.
    """
    try:
        gmail = GmailService()
        email = await gmail.get_email(email_id)
        return email
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice-command", response_model=CommandResponse)
async def handle_voice_command(command: VoiceCommand):
    """
    Process a voice command and perform the corresponding email action.
    """
    try:
        response = await process_voice_command(command.command)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emails/{email_id}/mark-read")
async def mark_email_read(email_id: str):
    """
    Mark an email as read.
    """
    try:
        gmail = GmailService()
        await gmail.mark_as_read(email_id)
        return {"success": True, "message": "Email marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emails/{email_id}/mark-unread")
async def mark_email_unread(email_id: str):
    """
    Mark an email as unread.
    """
    try:
        gmail = GmailService()
        await gmail.mark_as_unread(email_id)
        return {"success": True, "message": "Email marked as unread"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/emails/{email_id}/archive")
async def archive_email(email_id: str):
    """
    Archive an email.
    """
    try:
        gmail = GmailService()
        await gmail.archive_email(email_id)
        return {"success": True, "message": "Email archived"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 