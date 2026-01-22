#!/usr/bin/env python3
"""
Smartmail - Voice-Controlled Email Assistant
Main entry point for the application
"""

import os
import sys
import json
from datetime import datetime
from agent import start_agent

def check_credentials():
    """Check if Gmail API credentials are available"""
    if not os.path.exists('credentials/credentials.json'):
        print("Error: Gmail API credentials not found.")
        print("Please follow the setup instructions in README.md to set up your credentials.")
        return False
    return True

def main():
    """Main entry point for the application"""
    print("Starting Smartmail - Voice-Controlled Email Assistant")
    
    # Check if credentials are available
    if not check_credentials():
        sys.exit(1)
    
    try:
        # Run the agent
        start_agent()
    except KeyboardInterrupt:
        print("\nExiting Smartmail. Goodbye!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 