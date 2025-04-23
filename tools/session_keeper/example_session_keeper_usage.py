#!/usr/bin/env python3
"""
Example of using the SessionKeeper in your own applications.

This script demonstrates how to integrate the SessionKeeper into your own
applications to maintain a persistent authenticated session with the Fogis API.
"""

import os
import sys
import time
from fogis_session_keeper import SessionKeeper

# Replace with your actual credentials
USERNAME = os.environ.get("FOGIS_USERNAME", "your_username")
PASSWORD = os.environ.get("FOGIS_PASSWORD", "your_password")

def main():
    """Example of using the SessionKeeper."""
    print("Starting SessionKeeper example...")
    
    # Create and start the session keeper
    keeper = SessionKeeper(
        username=USERNAME,
        password=PASSWORD,
        check_interval=300,  # 5 minutes
        monitor_cookies=True,
        verbose=True
    )
    
    try:
        # Start the session keeper
        keeper.start()
        
        # Get the authenticated client
        client = keeper.get_client()
        
        # Example of using the client for API calls
        print("\nFetching matches list...")
        matches = client.fetch_matches_list()
        print(f"Found {len(matches)} matches")
        
        # Simulate a long-running application
        print("\nSimulating a long-running application...")
        print("The SessionKeeper will maintain the session in the background.")
        print("Press Ctrl+C to exit.")
        
        while True:
            # Every hour, do something with the authenticated client
            for i in range(12):  # 12 x 5 minutes = 1 hour
                time.sleep(300)  # 5 minutes
                
            # Use the client for API calls
            print("\nPerforming periodic API call...")
            matches = client.fetch_matches_list()
            print(f"Found {len(matches)} matches")
            
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        # Always stop the session keeper when done
        keeper.stop()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
