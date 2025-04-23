#!/usr/bin/env python3
"""
Fogis Session Keeper

This script maintains an active session with the Fogis API by periodically making
lightweight API calls and automatically re-authenticating when needed.

Usage:
    python fogis_session_keeper.py --username YOUR_USERNAME --password YOUR_PASSWORD [options]

Options:
    --interval SECONDS    Time between session checks in seconds (default: 300)
    --monitor             Monitor and log cookie changes
    --verbose             Enable verbose logging
"""

import argparse
import json
import logging
import os
import sys
import threading
import time
import smtplib
import platform
from datetime import datetime
from logging.handlers import RotatingFileHandler
from email.mime.text import MIMEText
from pathlib import Path

# Add the parent directory to the path so we can import the fogis_api_client
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from fogis_api_client import FogisApiClient
except ImportError:
    print("Error: Could not import FogisApiClient. Make sure the fogis-api-client package is installed.")
    sys.exit(1)


def send_notification(subject, message, email=None, desktop=True):
    """
    Send a notification via email and/or desktop notification.

    Args:
        subject (str): Notification subject
        message (str): Notification message
        email (str, optional): Email address to send notification to
        desktop (bool): Whether to show a desktop notification
    """
    # Log the notification
    logging.info(f"NOTIFICATION: {subject} - {message}")

    # Desktop notification
    if desktop:
        try:
            system = platform.system()
            if system == "Darwin":  # macOS
                os.system(f'osascript -e \'display notification "{message}" with title "{subject}"\'')
            elif system == "Linux":
                os.system(f'notify-send "{subject}" "{message}"')
            elif system == "Windows":
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(subject, message, duration=10)
        except Exception as e:
            logging.error(f"Failed to send desktop notification: {e}")

    # Email notification
    if email and os.environ.get("SMTP_SERVER") and os.environ.get("SMTP_FROM"):
        try:
            smtp_server = os.environ.get("SMTP_SERVER")
            smtp_port = int(os.environ.get("SMTP_PORT", 587))
            smtp_user = os.environ.get("SMTP_USER")
            smtp_pass = os.environ.get("SMTP_PASS")
            smtp_from = os.environ.get("SMTP_FROM")

            msg = MIMEText(message)
            msg['Subject'] = f"[Fogis Session Keeper] {subject}"
            msg['From'] = smtp_from
            msg['To'] = email

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            logging.info(f"Email notification sent to {email}")
        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")


class SessionKeeper:
    """Maintains an active session with the Fogis API."""

    def __init__(self, username=None, password=None, client=None, check_interval=300,
                 monitor_cookies=False, verbose=False, log_file=None,
                 notification_email=None, notify_on_changes=True):
        """
        Initialize the session keeper.

        Args:
            username (str, optional): Fogis username (not needed if client is provided)
            password (str, optional): Fogis password (not needed if client is provided)
            client (FogisApiClient, optional): Pre-authenticated client
            check_interval (int): Time between session checks in seconds (default: 5 minutes)
            monitor_cookies (bool): Whether to monitor and log cookie changes
            verbose (bool): Enable verbose logging
            log_file (str, optional): Path to log file
            notification_email (str, optional): Email to send notifications to
            notify_on_changes (bool): Whether to send notifications on cookie changes
        """
        self.username = username
        self.password = password
        self.check_interval = check_interval
        self.monitor_cookies = monitor_cookies
        self.notification_email = notification_email
        self.notify_on_changes = notify_on_changes

        # Set up logging
        log_level = logging.DEBUG if verbose else logging.INFO
        self.logger = logging.getLogger('fogis_session_keeper')
        self.logger.setLevel(log_level)
        self.logger.handlers = []  # Remove any existing handlers

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (if log_file is provided)
        if log_file:
            log_path = Path(log_file)
            log_dir = log_path.parent
            if not log_dir.exists():
                log_dir.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file, maxBytes=10*1024*1024, backupCount=5
            )
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

            self.logger.info(f"Logging to file: {log_file}")

        # Initialize the client
        if client:
            self.client = client
            self.logger.info("Using pre-authenticated client")
        elif username and password:
            self.client = FogisApiClient(username, password)
            self.logger.info("Created new client with username/password")
        else:
            raise ValueError("Either client or username/password must be provided")

        self.last_cookies = None
        self.running = False
        self.thread = None
        self.successful_checks = 0
        self.failed_checks = 0
        self.relogins = 0
        self.start_time = None
        self.last_activity_time = None

    def start(self):
        """Start the session keeper thread."""
        if self.running:
            self.logger.warning("Session keeper is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._session_keeper_loop)
        self.thread.daemon = True
        self.start_time = datetime.now()
        self.last_activity_time = self.start_time

        # Check if we need to login or if we already have a pre-authenticated client
        try:
            current_cookies = self.client.get_cookies()
            if current_cookies:
                self.logger.info("Client already has cookies, checking if they're valid...")
                try:
                    # Verify the cookies are valid
                    self.client.hello_world()
                    self.last_cookies = current_cookies
                    self.logger.info("Existing cookies are valid")

                    if self.monitor_cookies:
                        self.logger.debug(f"Initial cookies: {json.dumps(self.last_cookies, indent=2)}")

                    # Start the thread with existing cookies
                    self.thread.start()
                    self.logger.info(f"Session keeper started (check interval: {self.check_interval}s)")

                    # Send notification
                    if self.notify_on_changes:
                        send_notification(
                            "Session Keeper Started",
                            f"Session keeper started with existing cookies. Check interval: {self.check_interval}s",
                            email=self.notification_email
                        )
                    return
                except Exception:
                    self.logger.warning("Existing cookies are invalid, performing login...")

            # If we get here, we need to login
            if self.username and self.password:
                self.logger.info("Performing initial login...")
                self.client.login()
                self.last_cookies = self.client.get_cookies()
                self.logger.info("Initial login successful")

                if self.monitor_cookies:
                    self.logger.debug(f"Initial cookies: {json.dumps(self.last_cookies, indent=2)}")

                # Start the thread after successful login
                self.thread.start()
                self.logger.info(f"Session keeper started (check interval: {self.check_interval}s)")

                # Send notification
                if self.notify_on_changes:
                    send_notification(
                        "Session Keeper Started",
                        f"Session keeper started with new login. Check interval: {self.check_interval}s",
                        email=self.notification_email
                    )
            else:
                self.running = False
                error_msg = "Cannot login: No username/password provided and existing cookies are invalid"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

        except Exception as e:
            self.running = False
            self.logger.error(f"Initial setup failed: {str(e)}")

            # Send notification about failure
            if self.notify_on_changes:
                send_notification(
                    "Session Keeper Failed",
                    f"Failed to start session keeper: {str(e)}",
                    email=self.notification_email
                )
            raise

    def stop(self):
        """Stop the session keeper thread."""
        if not self.running:
            self.logger.warning("Session keeper is not running")
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.logger.info("Session keeper stopped")

        # Calculate runtime
        if self.start_time:
            runtime = datetime.now() - self.start_time
            hours, remainder = divmod(runtime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            runtime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        else:
            runtime_str = "unknown"

        # Print statistics
        stats_msg = (f"Session statistics: {self.successful_checks} successful checks, "
                    f"{self.failed_checks} failed checks, {self.relogins} relogins, "
                    f"runtime: {runtime_str}")
        self.logger.info(stats_msg)

        # Send notification
        if self.notify_on_changes:
            send_notification(
                "Session Keeper Stopped",
                stats_msg,
                email=self.notification_email
            )

    def _session_keeper_loop(self):
        """Main loop that keeps the session alive."""
        while self.running:
            time.sleep(self.check_interval)

            try:
                # Make a lightweight API call to keep the session alive
                self.logger.debug("Performing session check...")
                self.client.hello_world()
                self.successful_checks += 1
                self.last_activity_time = datetime.now()

                if self.monitor_cookies:
                    current_cookies = self.client.get_cookies()
                    if current_cookies != self.last_cookies:
                        cookie_change_msg = "Cookies have changed"
                        self.logger.info(cookie_change_msg)
                        self.logger.debug(f"New cookies: {json.dumps(current_cookies, indent=2)}")

                        # Send notification about cookie change
                        if self.notify_on_changes:
                            send_notification(
                                "Cookie Change Detected",
                                f"Cookies have changed after {self.successful_checks} successful checks",
                                email=self.notification_email
                            )

                        self.last_cookies = current_cookies
                    else:
                        self.logger.debug("No cookie changes detected")

                self.logger.info(f"Session check successful (total: {self.successful_checks})")

                # Write a status file with current statistics
                self._write_status_file()

            except Exception as e:
                self.failed_checks += 1
                error_msg = f"Session check failed: {str(e)}"
                self.logger.error(error_msg)

                # Send notification about session failure
                if self.notify_on_changes and self.failed_checks % 3 == 1:  # Only notify on 1st, 4th, 7th... failure
                    send_notification(
                        "Session Check Failed",
                        f"Session check failed: {str(e)}. This is failure #{self.failed_checks}.",
                        email=self.notification_email
                    )

                if self.username and self.password:
                    try:
                        # Try to login again
                        self.logger.info("Attempting to re-login...")
                        self.client.login()
                        self.relogins += 1
                        self.last_activity_time = datetime.now()

                        if self.monitor_cookies:
                            new_cookies = self.client.get_cookies()
                            self.logger.debug(f"New cookies after re-login: {json.dumps(new_cookies, indent=2)}")
                            self.last_cookies = new_cookies

                        relogin_msg = f"Re-login successful (total relogins: {self.relogins})"
                        self.logger.info(relogin_msg)

                        # Send notification about successful re-login
                        if self.notify_on_changes:
                            send_notification(
                                "Re-login Successful",
                                f"Successfully re-logged in after {self.failed_checks} failed checks.",
                                email=self.notification_email
                            )

                    except Exception as login_error:
                        login_error_msg = f"Re-login failed: {str(login_error)}"
                        self.logger.error(login_error_msg)

                        # Send notification about re-login failure
                        if self.notify_on_changes:
                            send_notification(
                                "Re-login Failed",
                                f"Failed to re-login: {str(login_error)}. This is critical!",
                                email=self.notification_email
                            )
                else:
                    self.logger.warning("Cannot re-login: No username/password provided")

                # Write status file with current statistics
                self._write_status_file()

    def get_client(self):
        """Get the authenticated client."""
        return self.client

    def get_status(self):
        """Get the current status of the session keeper."""
        if self.start_time:
            runtime = datetime.now() - self.start_time
            hours, remainder = divmod(runtime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            runtime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        else:
            runtime_str = "unknown"

        if self.last_activity_time:
            last_activity = datetime.now() - self.last_activity_time
            hours, remainder = divmod(last_activity.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            last_activity_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s ago"
        else:
            last_activity_str = "unknown"

        return {
            "running": self.running,
            "successful_checks": self.successful_checks,
            "failed_checks": self.failed_checks,
            "relogins": self.relogins,
            "runtime": runtime_str,
            "last_activity": last_activity_str,
            "check_interval": self.check_interval,
            "has_cookies": bool(self.last_cookies)
        }

    def _write_status_file(self):
        """Write current status to a status file."""
        try:
            status = self.get_status()
            status_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_keeper_status.json")
            with open(status_file, "w") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write status file: {str(e)}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Maintain an active session with the Fogis API")
    parser.add_argument("--username", help="Fogis username")
    parser.add_argument("--password", help="Fogis password")
    parser.add_argument("--cookies-file", help="Path to a JSON file containing cookies")
    parser.add_argument("--interval", type=int, default=300, help="Time between session checks in seconds (default: 300)")
    parser.add_argument("--monitor", action="store_true", help="Monitor and log cookie changes")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--log-file", help="Path to log file")
    parser.add_argument("--email", help="Email address for notifications")
    parser.add_argument("--no-notifications", action="store_true", help="Disable notifications")

    args = parser.parse_args()

    # Validate arguments
    if not args.cookies_file and not (args.username and args.password):
        print("Error: Either --cookies-file or both --username and --password must be provided")
        return 1

    try:
        # Create client
        client = None
        if args.cookies_file:
            try:
                with open(args.cookies_file, 'r') as f:
                    cookies = json.load(f)
                client = FogisApiClient(cookies=cookies)
                print(f"Loaded cookies from {args.cookies_file}")
            except Exception as e:
                print(f"Error loading cookies from file: {str(e)}")
                return 1

        # Create session keeper
        keeper = SessionKeeper(
            username=args.username,
            password=args.password,
            client=client,
            check_interval=args.interval,
            monitor_cookies=args.monitor or bool(args.email),  # Always monitor if email is provided
            verbose=args.verbose,
            log_file=args.log_file,
            notification_email=args.email,
            notify_on_changes=not args.no_notifications
        )

        keeper.start()

        # Keep the main thread alive with a simple loop
        print("\nSession keeper is running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping session keeper...")
            keeper.stop()

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
