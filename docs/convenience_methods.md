# Convenience Methods Guide

The FOGIS API Client provides a set of convenience methods that make common operations more intuitive and user-friendly. These methods build upon the solid OAuth 2.0 authentication foundation and provide a cleaner API surface.

## Overview

The convenience methods are designed to:
- **Simplify common operations** with intuitive method names
- **Aggregate data** from multiple endpoints in single calls
- **Provide structured responses** with consistent formatting
- **Handle errors gracefully** with comprehensive metadata
- **Maintain backward compatibility** while encouraging modern usage

## Core Convenience Methods

### `fetch_complete_match(match_id, include_optional=True)`

**The flagship convenience method** that fetches all match-related data in a single call.

```python
from fogis_api_client import PublicApiClient

client = PublicApiClient(username="your_username", password="your_password")

# Get complete match data in one call
match_data = client.fetch_complete_match(123456)

# Access different data types
print(f"Teams: {match_data['match_details']['lag1namn']} vs {match_data['match_details']['lag2namn']}")
print(f"Events: {len(match_data['events'])} events")
print(f"Home players: {len(match_data['players']['hemmalag'])} players")

# Check what was successfully fetched
metadata = match_data['metadata']
print(f"Successful endpoints: {list(metadata['success'].keys())}")
print(f"Warnings: {metadata['warnings']}")
```

**Benefits:**
- ✅ **Single call** instead of 5 separate API calls
- ✅ **Comprehensive data** including match details, players, officials, events, and results
- ✅ **Error resilience** - continues even if some endpoints fail
- ✅ **Rich metadata** with fetch status and timing information
- ✅ **Optional data control** - can exclude players/officials for faster responses

### `get_match_summary(match_id)`

Get essential match information in a clean, standardized format.

```python
# Get a concise match summary
summary = client.get_match_summary(123456)

print(f"{summary['home_team']} vs {summary['away_team']}")
print(f"Date: {summary['date']}, Status: {summary['status']}")
print(f"Final Score: {summary['final_score']}")
print(f"Venue: {summary['venue']}")
```

### `get_recent_matches(days=30, include_future=False)`

Fetch recent matches with simple date filtering.

```python
# Get matches from last 7 days
recent = client.get_recent_matches(days=7)
print(f"Found {len(recent)} matches in last 7 days")

# Include future matches
all_recent = client.get_recent_matches(days=30, include_future=True)
```

### `get_match_events_by_type(match_id, event_type=None)`

Organize match events by type for easier processing.

```python
# Get all events organized by type
events = client.get_match_events_by_type(123456)
print(f"Goals: {len(events['goals'])}")
print(f"Cards: {len(events['cards'])}")
print(f"Substitutions: {len(events['substitutions'])}")

# Get only specific event type
goals = client.get_match_events_by_type(123456, event_type='goals')
```

### `get_team_statistics(match_id)`

Get comprehensive team-level statistics.

```python
stats = client.get_team_statistics(123456)

home_stats = stats['home']
away_stats = stats['away']

print(f"{home_stats['team_name']}: {home_stats['goals']} goals, {home_stats['cards']} cards")
print(f"{away_stats['team_name']}: {away_stats['goals']} goals, {away_stats['cards']} cards")
```

## Search and Filter Methods

### `find_matches(**criteria)`

Intuitive match searching with multiple criteria.

```python
# Find matches by team name
team_matches = client.find_matches(team_name="IFK", limit=10)

# Find matches in date range
date_matches = client.find_matches(
    date_from="2025-01-01",
    date_to="2025-01-31",
    status=["klar"]
)

# Find matches by competition
league_matches = client.find_matches(competition="Allsvenskan")
```

### `get_matches_requiring_action()`

Identify matches that need attention.

```python
action_matches = client.get_matches_requiring_action()

print(f"Upcoming matches: {len(action_matches['upcoming'])}")
print(f"Needs reports: {len(action_matches['needs_report'])}")
print(f"Recently completed: {len(action_matches['recently_completed'])}")
```

## Migration from Legacy Methods

### Deprecated Methods (Still Functional)

The following methods are deprecated but continue to work with deprecation warnings:

```python
# ❌ DEPRECATED - Use new methods instead
match_details = client.fetch_match_json(123456)  # Use get_match_details() or fetch_complete_match()
players = client.fetch_match_players_json(123456)  # Use get_match_players() or fetch_complete_match()
officials = client.fetch_match_officials_json(123456)  # Use get_match_officials() or fetch_complete_match()
```

### Migration Examples

**Old approach (multiple calls):**
```python
# ❌ Old way - multiple API calls, complex error handling
try:
    match_details = client.fetch_match_json(123456)
    events = client.fetch_match_events_json(123456)
    players = client.fetch_match_players_json(123456)
    # Handle each potential failure separately...
except Exception as e:
    # Complex error handling for each endpoint
    pass
```

**New approach (single call):**
```python
# ✅ New way - single call, comprehensive data, built-in error handling
match_data = client.fetch_complete_match(123456)

# All data available with metadata about what succeeded/failed
if match_data['events']:
    print(f"Events: {len(match_data['events'])}")
if match_data['players']:
    print(f"Players: {len(match_data['players']['hemmalag'])} home, {len(match_data['players']['bortalag'])} away")

# Check for any issues
if match_data['metadata']['warnings']:
    print(f"Warnings: {match_data['metadata']['warnings']}")
```

## Error Handling and Resilience

The convenience methods are designed to be resilient:

```python
# fetch_complete_match continues even if some endpoints fail
match_data = client.fetch_complete_match(123456)

# Check what succeeded
successful = match_data['metadata']['success']
errors = match_data['metadata']['errors']
warnings = match_data['metadata']['warnings']

print(f"✅ Successful: {list(successful.keys())}")
if errors:
    print(f"❌ Errors: {list(errors.keys())}")
if warnings:
    print(f"⚠️ Warnings: {warnings}")
```

## Performance Considerations

### Optimizing API Calls

```python
# For quick overviews, disable optional data
quick_match = client.fetch_complete_match(123456, include_optional=False)
# Only fetches: match_details, events, result (3 endpoints instead of 5)

# For detailed analysis, include everything
full_match = client.fetch_complete_match(123456, include_optional=True)
# Fetches: match_details, events, result, players, officials (5 endpoints)
```

### Caching Considerations

```python
# Get recent matches once, then process multiple times
recent_matches = client.get_recent_matches(days=7)

for match in recent_matches:
    summary = client.get_match_summary(match['matchid'])
    # Process each match...
```

## Best Practices

### 1. Use Convenience Methods for New Code
```python
# ✅ Preferred for new development
complete_match = client.fetch_complete_match(match_id)
summary = client.get_match_summary(match_id)
recent = client.get_recent_matches(days=7)
```

### 2. Migrate Gradually from Legacy Methods
```python
# ✅ Gradual migration approach
import warnings

# Suppress deprecation warnings during migration
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    legacy_data = client.fetch_match_json(match_id)

# New code uses convenience methods
new_data = client.fetch_complete_match(match_id)
```

### 3. Handle Partial Failures Gracefully
```python
match_data = client.fetch_complete_match(match_id)

# Always check if optional data is available
if match_data['players']:
    # Process player data
    pass
else:
    print("Player data not available for this match")
```

### 4. Use Metadata for Debugging
```python
match_data = client.fetch_complete_match(match_id)
metadata = match_data['metadata']

# Log detailed information for debugging
logger.info(f"Fetch completed in {metadata['fetch_time']}")
logger.info(f"Successful endpoints: {list(metadata['success'].keys())}")

if metadata['warnings']:
    logger.warning(f"Warnings encountered: {metadata['warnings']}")
```

## Summary

The convenience methods provide a modern, intuitive interface to the FOGIS API while maintaining full backward compatibility. They are designed to:

- **Reduce complexity** by aggregating multiple API calls
- **Improve reliability** with built-in error handling
- **Enhance usability** with structured, consistent responses
- **Support migration** with clear deprecation paths

Start using these methods in new code and gradually migrate existing code to take advantage of the improved API design.
