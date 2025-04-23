#!/usr/bin/env python3
"""
Check Session Keeper Status

This script checks the status of the session keeper by reading the status file.

Usage:
    python check_session_status.py
"""

import json
import os
import sys
from datetime import datetime


def main():
    """Main entry point for the script."""
    status_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_keeper_status.json")
    
    if not os.path.exists(status_file):
        print("Error: Status file not found. Is the session keeper running?")
        return 1
        
    try:
        # Read status file
        with open(status_file, 'r') as f:
            status = json.load(f)
            
        # Print status
        print("=== Session Keeper Status ===")
        print(f"Running: {status['running']}")
        print(f"Successful checks: {status['successful_checks']}")
        print(f"Failed checks: {status['failed_checks']}")
        print(f"Relogins: {status['relogins']}")
        print(f"Runtime: {status['runtime']}")
        print(f"Last activity: {status['last_activity']}")
        print(f"Check interval: {status['check_interval']} seconds")
        print(f"Has cookies: {status['has_cookies']}")
        
        # Check if the session keeper is still active
        last_activity_parts = status['last_activity'].split()
        if len(last_activity_parts) >= 4 and last_activity_parts[1] == "h":
            hours = int(last_activity_parts[0])
            minutes = int(last_activity_parts[2])
            
            if hours > 0 or minutes > 10:
                print("\nWARNING: Session keeper may be inactive!")
                print(f"Last activity was {status['last_activity']}")
                
        print("\nFor more details, check the log file.")
        
    except Exception as e:
        print(f"Error reading status file: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
