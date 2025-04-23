# Fogis Session Keeper

This directory contains tools for maintaining persistent sessions with the Fogis API.

## Tools

### fogis_session_keeper.py

The main script that maintains a persistent session with the Fogis API by making periodic requests to keep the session alive.

```bash
python fogis_session_keeper.py --cookies-file cookies.json --interval 300 --monitor --log-file session.log
```

### save_fogis_cookies.py

A utility script to log in to Fogis and save the cookies to a file that can be used with the session keeper.

```bash
python save_fogis_cookies.py --username YOUR_USERNAME --password YOUR_PASSWORD --output cookies.json
```

### check_session_status.py

A utility script to check the status of a running session keeper.

```bash
python check_session_status.py
```

### example_session_keeper_usage.py

An example script showing how to integrate the session keeper into your own applications.

## Usage

1. Save cookies from a Fogis login:
   ```bash
   python save_fogis_cookies.py --username YOUR_USERNAME --password YOUR_PASSWORD
   ```

2. Start the session keeper with those cookies:
   ```bash
   python fogis_session_keeper.py --cookies-file fogis_cookies.json --interval 300 --monitor --log-file fogis_session.log
   ```

3. Monitor the session status:
   ```bash
   python check_session_status.py
   ```

## Advanced Usage

For long-running sessions, use a terminal multiplexer like `screen` or `tmux`:

```bash
screen -S fogis-session
python fogis_session_keeper.py --cookies-file fogis_cookies.json --interval 300 --monitor --log-file fogis_session.log
# Press Ctrl+A followed by D to detach
```

To reattach later:
```bash
screen -r fogis-session
```
