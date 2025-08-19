"""
Script to fetch sample data from the FOGIS API and anonymize it for use in tests.

This script uses the FOGIS API client to fetch real data, anonymizes it,
and saves it to a file that can be used by the mock server.

Usage:
    python scripts/fetch_sample_data.py

Environment variables:
    FOGIS_USERNAME: FOGIS username
    FOGIS_PASSWORD: FOGIS password
"""

import json
import logging
import os
import random
import string
from typing import Any, Dict

from fogis_api_client import FogisApiClient, configure_logging

# Configure logging
configure_logging(level="INFO")
logger = logging.getLogger(__name__)


def anonymize_string(text: str) -> str:
    """
    Anonymize a string by replacing it with a random string of the same length.

    Args:
        text: The string to anonymize

    Returns:
        An anonymized string
    """
    if not text:
        return text

    # For names, use a more realistic approach
    if len(text) < 20:
        if " " in text:  # Full name
            parts = text.split(" ")
            return " ".join(anonymize_string(part) for part in parts)

        # Generate a random string with the same first letter
        first_letter = text[0]
        rest = "".join(random.choices(string.ascii_lowercase, k=len(text) - 1))
        return first_letter + rest

    # For longer strings, just return a placeholder
    return f"Anonymized text ({len(text)} chars)"


def anonymize_match(match: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize a match object.

    Args:
        match: The match object to anonymize

    Returns:
        An anonymized match object
    """
    anonymized = match.copy()

    # Anonymize team names
    if "hemmalag" in anonymized:
        anonymized["hemmalag"] = f"Home Team {random.randint(1, 100)}"
    if "bortalag" in anonymized:
        anonymized["bortalag"] = f"Away Team {random.randint(1, 100)}"

    # Anonymize arena
    if "arena" in anonymized:
        anonymized["arena"] = f"Arena {random.randint(1, 50)}"

    # Anonymize people names
    for field in ["domare", "ad1", "ad2", "fjarde"]:
        if field in anonymized and anonymized[field]:
            anonymized[field] = anonymize_string(anonymized[field])

    # Anonymize notes
    if "notering" in anonymized and anonymized["notering"]:
        anonymized["notering"] = "Sample match notes"

    return anonymized


def anonymize_player(player: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize a player object.

    Args:
        player: The player object to anonymize

    Returns:
        An anonymized player object
    """
    anonymized = player.copy()

    # Anonymize names
    if "fornamn" in anonymized:
        anonymized["fornamn"] = f"Player"
    if "efternamn" in anonymized:
        anonymized["efternamn"] = f"{random.randint(1, 100)}"
    if "smeknamn" in anonymized and anonymized["smeknamn"]:
        anonymized["smeknamn"] = f"Nickname{random.randint(1, 10)}"

    # Anonymize license number
    if "licensnr" in anonymized and anonymized["licensnr"]:
        anonymized["licensnr"] = "".join(random.choices(string.ascii_uppercase, k=3)) + "".join(
            random.choices(string.digits, k=3)
        )

    return anonymized


def anonymize_official(official: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize an official object.

    Args:
        official: The official object to anonymize

    Returns:
        An anonymized official object
    """
    anonymized = official.copy()

    # Anonymize names
    if "fornamn" in anonymized:
        anonymized["fornamn"] = f"Official"
    if "efternamn" in anonymized:
        anonymized["efternamn"] = f"{random.randint(1, 50)}"

    return anonymized


def anonymize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize an event object.

    Args:
        event: The event object to anonymize

    Returns:
        An anonymized event object
    """
    anonymized = event.copy()

    # Anonymize player names
    if "spelare" in anonymized and anonymized["spelare"]:
        anonymized["spelare"] = f"Player {random.randint(1, 100)}"
    if "assisterande" in anonymized and anonymized["assisterande"]:
        anonymized["assisterande"] = f"Player {random.randint(1, 100)}"

    # Anonymize team name
    if "lag" in anonymized and anonymized["lag"]:
        if anonymized.get("lagid") == anonymized.get("hemmalagid", -1):
            anonymized["lag"] = "Home Team"
        else:
            anonymized["lag"] = "Away Team"

    return anonymized


def fetch_and_anonymize_data():
    """
    Fetch data from the FOGIS API and anonymize it.

    Returns:
        Dict with anonymized data
    """
    # Get credentials from environment variables
    username = os.environ.get("FOGIS_USERNAME")
    password = os.environ.get("FOGIS_PASSWORD")

    if not username or not password:
        raise ValueError("FOGIS_USERNAME and FOGIS_PASSWORD environment variables must be set")

    # Initialize the client
    client = FogisApiClient(username=username, password=password)
    logger.info("Logging in to FOGIS API...")
    client.login()
    logger.info("Login successful")

    # Fetch match list
    logger.info("Fetching match list...")
    matches = client.fetch_matches_list_json()
    logger.info(f"Found {len(matches)} matches")

    if not matches:
        raise ValueError("No matches found")

    # Select the first match for detailed data
    match_id = matches[0]["matchid"]
    logger.info(f"Using match ID {match_id} for detailed data")

    # Fetch match details
    logger.info("Fetching match details...")
    match = client.fetch_match_json(match_id)

    # Fetch match players
    logger.info("Fetching match players...")
    players = client.fetch_match_players_json(match_id)

    # Fetch match officials
    logger.info("Fetching match officials...")
    officials = client.fetch_match_officials_json(match_id)

    # Fetch match events
    logger.info("Fetching match events...")
    try:
        events = client.fetch_match_events_json(match_id)
    except Exception as e:
        logger.warning(f"Failed to fetch match events: {e}")
        events = []

    # Fetch match result
    logger.info("Fetching match result...")
    try:
        result = client.fetch_match_result_json(match_id)
    except Exception as e:
        logger.warning(f"Failed to fetch match result: {e}")
        result = {
            "matchid": match_id,
            "hemmamal": 2,
            "bortamal": 1,
            "halvtidHemmamal": 1,
            "halvtidBortamal": 0,
        }

    # Anonymize the data
    logger.info("Anonymizing data...")
    anonymized_matches = [anonymize_match(m) for m in matches[:5]]  # Take only first 5 matches
    anonymized_match = anonymize_match(match)

    anonymized_players = {
        "hemmalag": [anonymize_player(p) for p in players.get("hemmalag", [])[:5]],
        "bortalag": [anonymize_player(p) for p in players.get("bortalag", [])[:5]],
    }

    anonymized_officials = {
        "hemmalag": [anonymize_official(o) for o in officials.get("hemmalag", [])[:3]],
        "bortalag": [anonymize_official(o) for o in officials.get("bortalag", [])[:3]],
    }

    anonymized_events = [anonymize_event(e) for e in events[:5]]

    if isinstance(result, list):
        anonymized_result = anonymize_match(result[0]) if result else {}
    else:
        anonymized_result = anonymize_match(result)

    # Compile the data
    sample_data = {
        "SAMPLE_MATCH_LIST": {"matcher": anonymized_matches},
        "SAMPLE_MATCH": anonymized_match,
        "SAMPLE_MATCH_PLAYERS": anonymized_players,
        "SAMPLE_MATCH_OFFICIALS": anonymized_officials,
        "SAMPLE_MATCH_EVENTS": anonymized_events,
        "SAMPLE_MATCH_RESULT": anonymized_result,
    }

    return sample_data


def generate_python_file(data: Dict[str, Any], output_file: str = "integration_tests/sample_data.py"):
    """
    Generate a Python file with the sample data.

    Args:
        data: The data to include in the file
        output_file: The path to the output file
    """
    logger.info(f"Generating Python file: {output_file}")

    # Create the file content
    content = [
        '"""',
        "Sample data for the mock FOGIS API server.",
        "",
        "This module contains sample data structures that mimic the responses from the FOGIS API.",
        "The data is anonymized but follows the same structure as real API responses.",
        '"""',
        "",
    ]

    # Add each data structure
    for key, value in data.items():
        content.append(f"# {key}")
        content.append(f"{key} = {json.dumps(value, indent=4, ensure_ascii=False)}")
        content.append("")

    # Write the file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    logger.info(f"Sample data written to {output_file}")


if __name__ == "__main__":
    try:
        # Fetch and anonymize data
        sample_data = fetch_and_anonymize_data()

        # Generate Python file
        generate_python_file(sample_data)

        logger.info("Done!")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
