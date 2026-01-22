from typing import Dict, Any
from ..models.email import CommandResponse
import re

async def process_voice_command(command: str) -> CommandResponse:
    """
    Process voice commands and return appropriate responses.
    """
    command = command.lower().strip()
    
    # Command patterns
    patterns = {
        'read_email': r'read (email|mail)( number)? (\d+)',
        'next_email': r'(next|forward)( email| mail)?',
        'previous_email': r'(previous|back)( email| mail)?',
        'mark_read': r'mark( as)? read',
        'mark_unread': r'mark( as)? unread',
        'archive': r'archive( this)?( email| mail)?',
        'inbox': r'(go to |show |open )?inbox',
        'refresh': r'refresh|reload',
    }
    
    # Check each pattern
    for action, pattern in patterns.items():
        match = re.search(pattern, command)
        if match:
            return create_command_response(action, match)
    
    # Handle unrecognized commands
    return CommandResponse(
        success=False,
        message="Sorry, I didn't understand that command.",
        action="unknown"
    )

def create_command_response(action: str, match: re.Match) -> CommandResponse:
    """
    Create appropriate response based on the matched command.
    """
    responses = {
        'read_email': {
            'success': True,
            'message': f"Reading email {match.group(3)}",
            'action': 'read_email',
            'data': {'email_number': int(match.group(3))}
        },
        'next_email': {
            'success': True,
            'message': "Moving to next email",
            'action': 'next_email'
        },
        'previous_email': {
            'success': True,
            'message': "Moving to previous email",
            'action': 'previous_email'
        },
        'mark_read': {
            'success': True,
            'message': "Marking email as read",
            'action': 'mark_read'
        },
        'mark_unread': {
            'success': True,
            'message': "Marking email as unread",
            'action': 'mark_unread'
        },
        'archive': {
            'success': True,
            'message': "Archiving email",
            'action': 'archive'
        },
        'inbox': {
            'success': True,
            'message': "Opening inbox",
            'action': 'show_inbox'
        },
        'refresh': {
            'success': True,
            'message': "Refreshing emails",
            'action': 'refresh'
        }
    }
    
    response_data = responses.get(action, {
        'success': False,
        'message': "Command not implemented",
        'action': 'unknown'
    })
    
    return CommandResponse(**response_data) 