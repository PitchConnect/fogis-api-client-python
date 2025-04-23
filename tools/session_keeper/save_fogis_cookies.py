#!/usr/bin/env python3
"""
Save Fogis Cookies

This script logs in to Fogis and saves the cookies to a file that can be used
with the session keeper.

Usage:
    python save_fogis_cookies.py --username YOUR_USERNAME --password YOUR_PASSWORD [--output cookies.json]
"""

import argparse
import json
import os
import sys

# Add the parent directory to the path so we can import the fogis_api_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fogis_api_client import FogisApiClient
except ImportError:
    print("Error: Could not import FogisApiClient. Make sure the fogis-api-client package is installed.")
    sys.exit(1)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Save Fogis cookies to a file")
    parser.add_argument("--username", required=True, help="Fogis username")
    parser.add_argument("--password", required=True, help="Fogis password")
    parser.add_argument("--output", default="fogis_cookies.json", help="Output file path (default: fogis_cookies.json)")
    
    args = parser.parse_args()
    
    try:
        # Create client and login
        client = FogisApiClient(args.username, args.password)
        print(f"Logging in as {args.username}...")
        client.login()
        
        # Get cookies
        cookies = client.get_cookies()
        if not cookies:
            print("Error: No cookies returned after login")
            return 1
            
        # Save cookies to file
        with open(args.output, 'w') as f:
            json.dump(cookies, f, indent=2)
            
        print(f"Cookies saved to {args.output}")
        print("\nYou can now use these cookies with the session keeper:")
        print(f"python fogis_session_keeper.py --cookies-file {args.output} --interval 300 --monitor --log-file fogis_session.log")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
