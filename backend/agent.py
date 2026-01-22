from langchain.agents import create_react_agent
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor
from langchain.prompts import PromptTemplate
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
from tools.agent_tools import build_agent_tools
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import pyttsx3

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='logs/agent.log',
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_email_state():
    """Load the current email state from memory"""
    try:
        with open('memory/email_state.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default state if file doesn't exist or is invalid
        return {
            "last_read_date": datetime.now().strftime('%Y-%m-%d'),
            "read_emails": [],
            "current_label": "INBOX",
            "current_date": "today",
            "current_email_index": 0
        }

def save_email_state(state):
    """Save the current email state to memory"""
    os.makedirs('memory', exist_ok=True)
    with open('memory/email_state.json', 'w') as f:
        json.dump(state, f, indent=2)

def greet_user():
    """Greet the user and announce unread emails"""
    state = load_email_state()
    unread_count = len(fetch_unread_emails(label=state["current_label"], date=state["current_date"]))
    greeting = f"Hello! You have {unread_count} unread emails in your {state['current_label'].lower()}."
    speak(greeting)
    logging.info(f"Found {unread_count} unread emails in {state['current_label'].lower()}")
    return greeting

def process_email(email_id, state):
    """Process a single email based on user commands"""
    # Read subject and sender
    email_info = read_subject_sender(email_id)
    speak(email_info)
    logging.info(f"Reading email: {email_info}")
    
    # Wait for user command
    while True:
        speak("What would you like to do? Say 'continue' to read the full body, 'skip' to go to the next email, or 'back' to go to the previous email.")
        command = listen_command()
        action = process_command(command)
        logging.info(f"User command: {command} (interpreted as: {action})")
        
        if action == "continue":
            # Read full body
            body = read_body(email_id)
            speak(body)
            logging.info("Reading email body")
            break
        elif action == "skip":
            # Mark as unread and go to next
            mark_as_unread(email_id)
            logging.info("Marking email as unread and moving to next")
            break
        elif action == "back":
            # Go back to previous email
            if state["current_email_index"] > 0:
                state["current_email_index"] -= 1
                logging.info("Moving to previous email")
                return state
            else:
                speak("You're at the first email.")
                logging.info("User tried to go back from first email")
                break
        elif action == "important":
            # Mark as important
            mark_as_important(email_id)
            speak("Email marked as important.")
            logging.info("Marking email as important")
            break
        elif action == "promotions":
            # Switch to promotions
            state["current_label"] = "CATEGORY_PROMOTIONS"
            state["current_date"] = "today"
            state["current_email_index"] = 0
            save_email_state(state)
            unread_count = len(fetch_unread_emails(label='CATEGORY_PROMOTIONS', date='today'))
            speak(f"Switching to Promotions. You have {unread_count} unread emails.")
            logging.info(f"Switching to Promotions label. Found {unread_count} unread emails.")
            return state
        elif action == "quit":
            # Quit the program
            speak("Goodbye!")
            logging.info("User quit the program")
            return None
        else:
            speak("I didn't understand that command. Please try again.")
            logging.warning(f"Unknown command: {command}")
    
    # Move to next email
    state["current_email_index"] += 1
    logging.info("Moving to next email")
    return state

def process_emails(state):
    """Process all emails in the current label and date"""
    # Get unread emails
    emails = fetch_unread_emails(label=state["current_label"], date=state["current_date"])
    
    if not emails:
        if state["current_date"] == "today":
            # If no emails today, check yesterday
            state["current_date"] = "yesterday"
            state["current_email_index"] = 0
            save_email_state(state)
            speak("No more unread emails for today. Checking yesterday's emails.")
            logging.info("No more unread emails for today. Checking yesterday's emails.")
            return process_emails(state)
        else:
            speak("No more unread emails.")
            logging.info("No more unread emails.")
            return state
    
    # Process current email
    if state["current_email_index"] < len(emails):
        email_id = emails[state["current_email_index"]]["id"]
        speak(f"This is the next email...")
        logging.info(f"Processing email {state['current_email_index'] + 1} of {len(emails)}")
        return process_email(email_id, state)
    else:
        # If we've processed all emails for today, check yesterday
        if state["current_date"] == "today":
            state["current_date"] = "yesterday"
            state["current_email_index"] = 0
            save_email_state(state)
            speak("No more unread emails for today. Checking yesterday's emails.")
            logging.info("No more unread emails for today. Checking yesterday's emails.")
            return process_emails(state)
        else:
            speak("No more unread emails.")
            logging.info("No more unread emails.")
            return state

# Initialize the agent with tools
tools = build_agent_tools()
llm = Ollama(model="llama3")

# Create the prompt template
prompt = PromptTemplate.from_template(
    """You are a helpful email assistant that can read and manage emails.

Available tools: {tool_names}

To solve the task, you can use these tools: {tools}

Please help with the following request: {input}

Think through this step by step:
1) First, understand what is being asked
2) Then, decide which tool would be most helpful
3) Finally, use the tool and explain what you found

{agent_scratchpad}

Remember to be clear and helpful in your responses."""
)

# Create the agent
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

# Create the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

async def process_voice_command(command: str):
    """Process a voice command and return the appropriate response"""
    try:
        command = command.lower().strip()
        state = load_email_state()
        response = {"action": "UNKNOWN", "data": None, "speech_response": ""}

        if command == "start":
            # Initialize and get unread count
            emails = fetch_unread_emails(label=state["current_label"], date=state["current_date"])
            response = {
                "action": "START",
                "data": {"unread_count": len(emails)},
                "speech_response": f"Hello! You have {len(emails)} unread emails in your inbox."
            }
        
        elif command == "continue":
            # Read the current email's body
            emails = fetch_unread_emails(label=state["current_label"], date=state["current_date"])
            if state["current_email_index"] < len(emails):
                email_id = emails[state["current_email_index"]]["id"]
                body = read_body(email_id)
                response = {
                    "action": "READ_EMAIL",
                    "data": {"body": body},
                    "speech_response": body
                }
            else:
                response["speech_response"] = "No more emails to read."

        elif command == "stop this mail":
            response = {
                "action": "STOP_READING",
                "data": None,
                "speech_response": "Stopped reading the current email."
            }

        elif command == "continue with the next one":
            # Move to next email
            state["current_email_index"] += 1
            save_email_state(state)
            
            emails = fetch_unread_emails(label=state["current_label"], date=state["current_date"])
            if state["current_email_index"] < len(emails):
                email = emails[state["current_email_index"]]
                email_info = read_subject_sender(email["id"])
                response = {
                    "action": "NEXT_EMAIL",
                    "data": {"email_info": email_info},
                    "speech_response": f"Next email: {email_info}"
                }
            else:
                response["speech_response"] = "No more emails to read."

        else:
            response["speech_response"] = "I didn't understand that command. Available commands are: start, continue, stop this mail, continue with the next one"

        return response
            
    except Exception as e:
        logging.error(f"Error processing command: {str(e)}")
        return {
            "action": "ERROR",
            "data": {"error": str(e)},
            "speech_response": "Sorry, an error occurred while processing your command."
        }

async def start_agent():
    """Initialize the email assistant"""
    try:
        # Ensure directories exist
        os.makedirs('memory', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Load initial state
        state = load_email_state()
        
        # Get unread count
        try:
            emails = fetch_unread_emails(label=state["current_label"], date=state["current_date"])
            email_count = len(emails)
        except Exception as e:
            logging.error(f"Could not fetch emails: {str(e)}")
            email_count = 0
        
        # Initialize text-to-speech engine
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 1.0)
        except Exception as e:
            logging.error(f"Failed to initialize text-to-speech engine: {str(e)}")
            return {
                "status": "error",
                "message": "Failed to initialize text-to-speech engine",
                "speech_response": "Sorry, I couldn't initialize the text-to-speech engine."
            }
        
        return {
            "status": "success",
            "message": "Email assistant initialized successfully",
            "speech_response": f"Hello! I'm ready to help you with your emails. You have {email_count} unread emails in your inbox. Say 'start' when you're ready to begin."
        }
    except Exception as e:
        logging.error(f"Error starting agent: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "speech_response": "Sorry, I encountered an error while initializing. Please try again."
        }

def speak(text):
    engine = pyttsx3.init()  # Auto-picks SAPI5 on Windows
    engine.say(text)
    engine.runAndWait()

if __name__ == "__main__":
    start_agent() 