"""
Event types definitions for FOGIS API client.

This module contains the definitions of event types used in match reporting.
"""

from typing import Any, Dict

# Event types dictionary for match events
EVENT_TYPES: Dict[int, Dict[str, Any]] = {
    # Goals
    6: {"name": "Regular Goal", "goal": True},
    39: {"name": "Header Goal", "goal": True},
    28: {"name": "Corner Goal", "goal": True},
    29: {"name": "Free Kick Goal", "goal": True},
    15: {"name": "Own Goal", "goal": True},
    14: {"name": "Penalty Goal", "goal": True},
    # Penalties
    18: {"name": "Penalty Missing Goal", "goal": False},
    19: {"name": "Penalty Save", "goal": False},
    26: {"name": "Penalty Hitting the Frame", "goal": False},
    # Cards
    20: {"name": "Yellow Card", "goal": False},
    8: {"name": "Red Card (Denying Goal Opportunity)", "goal": False},
    9: {"name": "Red Card (Other Reasons)", "goal": False},
    # Other events
    17: {"name": "Substitution", "goal": False},
    # Control events
    31: {"name": "Period Start", "goal": False, "control_event": True},
    32: {"name": "Period End", "goal": False, "control_event": True},
    23: {"name": "Match Slut", "goal": False, "control_event": True},
}
