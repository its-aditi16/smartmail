from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EmailBase(BaseModel):
    subject: str
    sender: str
    date: str
    is_unread: bool

class EmailCreate(EmailBase):
    body: str

class EmailResponse(EmailBase):
    id: str
    snippet: Optional[str] = None

class EmailList(BaseModel):
    emails: List[EmailResponse]
    total: int
    unread_count: int

class EmailDetail(EmailResponse):
    body: str
    labels: List[str]

class VoiceCommand(BaseModel):
    command: str

class CommandResponse(BaseModel):
    success: bool
    message: str
    action: Optional[str] = None
    data: Optional[dict] = None 