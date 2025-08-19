# FOGIS API Client - Filter Guide

This comprehensive guide covers the powerful filtering capabilities of the FOGIS API Client, including how to fetch historic data, filter by various criteria, and optimize your queries.

## Table of Contents

- [Overview](#overview)
- [Basic Filtering](#basic-filtering)
- [Date Range Filtering](#date-range-filtering)
- [Status Filtering](#status-filtering)
- [Category and Type Filtering](#category-and-type-filtering)
- [Complex Filtering](#complex-filtering)
- [Historic Data Fetching](#historic-data-fetching)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

## Overview

The `MatchListFilter` class provides a fluent API for building complex filter criteria to query matches from the FOGIS API. It supports both server-side filtering (more efficient) and client-side filtering (more flexible).

### Key Features

- **Fluent API**: Chainable methods for building filters
- **Server-side Filtering**: Efficient filtering at the API level
- **Client-side Filtering**: Additional filtering after data retrieval
- **Type Safety**: Full enum support for filter values
- **Flexible Combinations**: Mix and match different filter types

## Basic Filtering

### Creating a Filter

```python
from fogis_api_client import MatchListFilter, FogisApiClient

# Create a new filter instance
filter = MatchListFilter()

# Create client instance
client = FogisApiClient(username="your_username", password="your_password")

# Fetch filtered matches
matches = filter.fetch_filtered_matches(client)
```

### Simple Filter Example

```python
from fogis_api_client.enums import MatchStatus

# Filter for only completed matches
completed_matches = (MatchListFilter()
    .include_statuses([MatchStatus.COMPLETED])
    .fetch_filtered_matches(client))

print(f"Found {len(completed_matches)} completed matches")
```

## Date Range Filtering

Date range filtering is one of the most common and powerful filtering options, especially for fetching historic data.

### Basic Date Range

```python
from datetime import datetime, timedelta

# Get matches from the last 30 days
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

recent_matches = (MatchListFilter()
    .start_date(start_date)
    .end_date(end_date)
    .fetch_filtered_matches(client))
```

### Specific Date Ranges

```python
# Get matches from a specific month (January 2024)
january_matches = (MatchListFilter()
    .start_date("2024-01-01")
    .end_date("2024-01-31")
    .fetch_filtered_matches(client))

# Get matches from last week
last_week_start = (datetime.now() - timedelta(weeks=1)).strftime('%Y-%m-%d')
last_week_matches = (MatchListFilter()
    .start_date(last_week_start)
    .end_date(datetime.now().strftime('%Y-%m-%d'))
    .fetch_filtered_matches(client))
```

### Future Matches

```python
# Get upcoming matches for the next 2 weeks
today = datetime.now().strftime('%Y-%m-%d')
two_weeks_later = (datetime.now() + timedelta(weeks=2)).strftime('%Y-%m-%d')

upcoming_matches = (MatchListFilter()
    .start_date(today)
    .end_date(two_weeks_later)
    .fetch_filtered_matches(client))
```

## Status Filtering

Filter matches based on their current status using the `MatchStatus` enum.

### Available Match Statuses

```python
from fogis_api_client.enums import MatchStatus

# Available statuses:
# MatchStatus.COMPLETED - "genomford" (finished matches)
# MatchStatus.CANCELLED - "installd" (cancelled matches)
# MatchStatus.POSTPONED - "uppskjuten" (postponed matches)
# MatchStatus.INTERRUPTED - "avbruten" (interrupted matches)
# MatchStatus.NOT_STARTED - "ej_startad" (not yet started)
```

### Include Specific Statuses

```python
# Get only completed matches
completed = (MatchListFilter()
    .include_statuses([MatchStatus.COMPLETED])
    .fetch_filtered_matches(client))

# Get problematic matches (cancelled or postponed)
problematic = (MatchListFilter()
    .include_statuses([MatchStatus.CANCELLED, MatchStatus.POSTPONED])
    .fetch_filtered_matches(client))
```

### Exclude Specific Statuses

```python
# Get all matches except cancelled ones
non_cancelled = (MatchListFilter()
    .exclude_statuses([MatchStatus.CANCELLED])
    .fetch_filtered_matches(client))

# Exclude both cancelled and postponed matches
active_matches = (MatchListFilter()
    .exclude_statuses([MatchStatus.CANCELLED, MatchStatus.POSTPONED])
    .fetch_filtered_matches(client))
```

## Category and Type Filtering

Filter matches by age category, gender, and football type.

### Age Category Filtering

```python
from fogis_api_client.enums import AgeCategory

# Available age categories:
# AgeCategory.CHILDREN (2)
# AgeCategory.YOUTH (3)
# AgeCategory.SENIOR (4)
# AgeCategory.VETERANS (5)
# AgeCategory.UNDEFINED (1)

# Get only youth matches
youth_matches = (MatchListFilter()
    .include_age_categories([AgeCategory.YOUTH])
    .fetch_filtered_matches(client))

# Get senior and veteran matches
adult_matches = (MatchListFilter()
    .include_age_categories([AgeCategory.SENIOR, AgeCategory.VETERANS])
    .fetch_filtered_matches(client))

# Exclude children's matches
non_children = (MatchListFilter()
    .exclude_age_categories([AgeCategory.CHILDREN])
    .fetch_filtered_matches(client))
```

### Gender Filtering

```python
from fogis_api_client.enums import Gender

# Available genders:
# Gender.MALE (2)
# Gender.FEMALE (3)
# Gender.MIXED (4)

# Get only women's matches
womens_matches = (MatchListFilter()
    .include_genders([Gender.FEMALE])
    .fetch_filtered_matches(client))

# Get men's and mixed matches
mens_and_mixed = (MatchListFilter()
    .include_genders([Gender.MALE, Gender.MIXED])
    .fetch_filtered_matches(client))
```

### Football Type Filtering

```python
from fogis_api_client.enums import FootballType

# Available football types:
# FootballType.FOOTBALL (1) - Outdoor football
# FootballType.FUTSAL (2) - Indoor futsal

# Get only outdoor football matches
outdoor_matches = (MatchListFilter()
    .include_football_types([FootballType.FOOTBALL])
    .fetch_filtered_matches(client))

# Get only futsal matches
futsal_matches = (MatchListFilter()
    .include_football_types([FootballType.FUTSAL])
    .fetch_filtered_matches(client))
```

## Complex Filtering

Combine multiple filter types for sophisticated queries.

### Multi-Criteria Filtering

```python
# Get completed youth football matches from last month
last_month = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
today = datetime.now().strftime('%Y-%m-%d')

youth_completed = (MatchListFilter()
    .start_date(last_month)
    .end_date(today)
    .include_statuses([MatchStatus.COMPLETED])
    .include_age_categories([AgeCategory.YOUTH])
    .include_football_types([FootballType.FOOTBALL])
    .fetch_filtered_matches(client))
```

### Exclusion-based Filtering

```python
# Get all matches except cancelled children's futsal matches
filtered_matches = (MatchListFilter()
    .exclude_statuses([MatchStatus.CANCELLED])
    .exclude_age_categories([AgeCategory.CHILDREN])
    .exclude_football_types([FootballType.FUTSAL])
    .fetch_filtered_matches(client))
```

### Mixed Include/Exclude Filtering

```python
# Get completed or interrupted senior/veteran men's matches, excluding futsal
complex_filter = (MatchListFilter()
    .include_statuses([MatchStatus.COMPLETED, MatchStatus.INTERRUPTED])
    .include_age_categories([AgeCategory.SENIOR, AgeCategory.VETERANS])
    .include_genders([Gender.MALE])
    .exclude_football_types([FootballType.FUTSAL])
    .fetch_filtered_matches(client))
```

## Historic Data Fetching

Specialized patterns for fetching and analyzing historic match data.

### Season Analysis

```python
# Get all matches from the 2023 season
season_2023 = (MatchListFilter()
    .start_date("2023-01-01")
    .end_date("2023-12-31")
    .fetch_filtered_matches(client))

# Analyze completed matches by month
completed_2023 = (MatchListFilter()
    .start_date("2023-01-01")
    .end_date("2023-12-31")
    .include_statuses([MatchStatus.COMPLETED])
    .fetch_filtered_matches(client))

print(f"Completed {len(completed_2023)} matches in 2023")
```

### Monthly Reports

```python
def get_monthly_matches(year, month, client):
    """Get all matches for a specific month."""
    import calendar

    # Get the last day of the month
    last_day = calendar.monthrange(year, month)[1]

    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"

    return (MatchListFilter()
        .start_date(start_date)
        .end_date(end_date)
        .fetch_filtered_matches(client))

# Get matches for March 2024
march_matches = get_monthly_matches(2024, 3, client)
```

### Performance Analysis

```python
# Get all completed matches to analyze performance
all_completed = (MatchListFilter()
    .include_statuses([MatchStatus.COMPLETED])
    .fetch_filtered_matches(client))

# Analyze by category
youth_completed = [m for m in all_completed if m.get('tavlingAlderskategori') == AgeCategory.YOUTH.value]
senior_completed = [m for m in all_completed if m.get('tavlingAlderskategori') == AgeCategory.SENIOR.value]

print(f"Youth matches: {len(youth_completed)}")
print(f"Senior matches: {len(senior_completed)}")
```

## Performance Optimization

### Server-side vs Client-side Filtering

```python
# EFFICIENT: Server-side filtering (recommended)
# Date ranges, status, age category, gender are filtered server-side
efficient_filter = (MatchListFilter()
    .start_date("2024-01-01")
    .end_date("2024-01-31")
    .include_statuses([MatchStatus.COMPLETED]))

# The filter builds a minimal payload and sends it to the server
payload = efficient_filter.build_payload()
print(payload)  # Only includes configured filters

# LESS EFFICIENT: Fetching all data then filtering client-side
all_matches = client.fetch_matches_list_json()
completed_matches = [m for m in all_matches if m.get('arslutresultat')]
```

### Batch Processing

```python
def process_matches_in_batches(start_date, end_date, client, batch_days=7):
    """Process matches in weekly batches for large date ranges."""
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    all_matches = []

    while current_date <= end_date_obj:
        batch_end = min(current_date + timedelta(days=batch_days), end_date_obj)

        batch_matches = (MatchListFilter()
            .start_date(current_date.strftime('%Y-%m-%d'))
            .end_date(batch_end.strftime('%Y-%m-%d'))
            .fetch_filtered_matches(client))

        all_matches.extend(batch_matches)
        current_date = batch_end + timedelta(days=1)

    return all_matches

# Process a full year in weekly batches
year_matches = process_matches_in_batches("2023-01-01", "2023-12-31", client)
```

## Troubleshooting

### Common Issues and Solutions

#### Empty Results

```python
# Problem: Filter returns no matches
filter = MatchListFilter().include_statuses([MatchStatus.COMPLETED])
matches = filter.fetch_filtered_matches(client)

if not matches:
    # Try broader criteria
    broader_filter = MatchListFilter()  # No filters = all matches
    all_matches = broader_filter.fetch_filtered_matches(client)
    print(f"Total available matches: {len(all_matches)}")
```

#### Date Range Issues

```python
# Problem: Invalid date format
try:
    filter = MatchListFilter().start_date("2024-1-1")  # Wrong format
except Exception as e:
    print(f"Use YYYY-MM-DD format: {e}")

# Solution: Use proper date format
filter = MatchListFilter().start_date("2024-01-01")  # Correct format
```

#### Performance Issues

```python
# Problem: Slow queries with large date ranges
# Solution: Use smaller date ranges or server-side filtering

# Instead of this (slow):
large_range = (MatchListFilter()
    .start_date("2020-01-01")
    .end_date("2024-12-31")
    .fetch_filtered_matches(client))

# Do this (faster):
recent_range = (MatchListFilter()
    .start_date("2024-01-01")
    .end_date("2024-12-31")
    .include_statuses([MatchStatus.COMPLETED])  # Server-side filter
    .fetch_filtered_matches(client))
```

### Debug Information

```python
# Check what payload is being sent to the server
filter = (MatchListFilter()
    .start_date("2024-01-01")
    .include_statuses([MatchStatus.COMPLETED]))

payload = filter.build_payload()
print(f"Server payload: {payload}")

# This helps debug server-side vs client-side filtering
```

## Best Practices

1. **Use server-side filtering when possible** - More efficient
2. **Combine filters logically** - Don't over-filter
3. **Use appropriate date ranges** - Avoid unnecessarily large ranges
4. **Cache results when appropriate** - For repeated queries
5. **Handle empty results gracefully** - Always check for empty lists
6. **Use enums for type safety** - Avoid magic strings/numbers

For more examples and advanced usage, see the [API Reference](api_reference.md) and [test files](../tests/test_match_list_filter.py).
