"""
Agent Tools Module

This module wraps all the mail and voice tools as LangChain tools.
"""

from langchain.agents import Tool
from tools.mail_tools import (
    fetch_unread_emails,
    read_subject_sender,
    read_body,
    mark_as_unread,
    mark_as_important,
    switch_label,
    get_yesterday_unreads
)
from tools.voice_tools import speak, listen_command, process_command

def build_agent_tools():
    """
    Builds and returns a list of LangChain tools.
    
    Returns:
        list: A list of Tool objects for the LangChain agent.
    """
    tools = [
        Tool(
            name="FetchInboxToday",
            func=fetch_unread_emails,
            description="Fetches unread emails from inbox for today"
        ),
        Tool(
            name="ReadTop",
            func=read_subject_sender,
            description="Reads the subject and sender of an email"
        ),
        Tool(
            name="ReadBody",
            func=read_body,
            description="Reads the full body of an email"
        ),
        Tool(
            name="MarkUnread",
            func=mark_as_unread,
            description="Marks an email as unread"
        ),
        Tool(
            name="MarkImportant",
            func=mark_as_important,
            description="Marks an email as important"
        ),
        Tool(
            name="SwitchLabel",
            func=switch_label,
            description="Switches to a different email label (e.g., Promotions)"
        ),
        Tool(
            name="GetYesterday",
            func=get_yesterday_unreads,
            description="Gets unread emails from yesterday"
        ),
        Tool(
            name="Speak",
            func=speak,
            description="Speaks the given text"
        ),
        Tool(
            name="Listen",
            func=listen_command,
            description="Listens for user command"
        ),
        Tool(
            name="ProcessCommand",
            func=process_command,
            description="Processes a voice command and returns the appropriate action"
        )
    ]
    
    return tools 