# AI Development Guidelines

## Introduction

This document provides guidelines for AI-assisted development with the FOGIS API client. As AI tools become more common in our development workflow, we need specific safeguards to prevent unintended modifications to critical code sections.

## AI-Safe Code Markers

Throughout the codebase, you will find special comment blocks that mark critical code sections:

```python
# AI-CRITICAL-SECTION-START
# WARNING: This code section maintains critical API contracts.
# Do not modify the structure of data sent to the API without understanding
# the server requirements. See docs/api_contracts.md for details.
# [Additional context-specific information]
# AI-CRITICAL-SECTION-END
```

These markers indicate code that:
1. Interfaces directly with the FOGIS API
2. Maintains critical API contracts
3. Has specific structure requirements
4. Should not be modified without careful consideration

## Guidelines for AI Tools

If you are an AI assistant helping with development:

1. **Respect AI-Safe Markers**:
   - Do not modify the structure of data sent to the API in marked sections
   - Preserve the exact field names and data types required by the API
   - If changes are needed, suggest them with clear warnings about potential impacts

2. **Understand API Contracts**:
   - Before modifying any API-related code, review the API documentation
   - Pay special attention to the structure of request and response data
   - Ensure any changes maintain backward compatibility

3. **When in Doubt, Ask**:
   - If you're unsure about modifying a critical section, ask for clarification
   - Suggest alternatives that preserve the API contract
   - Highlight potential risks in your suggestions

## Examples of Safe and Unsafe Modifications

### Safe Modifications

```python
# Original code
def report_match_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
    # AI-CRITICAL-SECTION-START
    # ...
    # AI-CRITICAL-SECTION-END

    # Process result data
    response_data = self._api_request(url, result_data_copy)
    return response_data

# Safe modification: Adding logging
def report_match_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
    # AI-CRITICAL-SECTION-START
    # ...
    # AI-CRITICAL-SECTION-END

    # Process result data
    self.logger.info(f"Reporting match result for match ID: {result_data.get('matchid')}")
    response_data = self._api_request(url, result_data_copy)
    return response_data
```

### Unsafe Modifications

```python
# Original code
def report_match_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
    # AI-CRITICAL-SECTION-START
    # ...
    # AI-CRITICAL-SECTION-END

    # Convert flat structure to nested structure
    result_data_copy = {
        "matchresultatListaJSON": [
            {
                "matchid": match_id,
                "matchresultattypid": 1,  # Full time
                "matchlag1mal": fulltime_home,
                "matchlag2mal": fulltime_away,
                "wo": False,
                "ow": False,
                "ww": False
            },
            # ...
        ]
    }

    response_data = self._api_request(url, result_data_copy)
    return response_data

# UNSAFE modification: Changing API data structure
def report_match_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
    # AI-CRITICAL-SECTION-START
    # ...
    # AI-CRITICAL-SECTION-END

    # Convert flat structure to a different structure (BREAKING CHANGE!)
    result_data_copy = {
        "matchResults": [  # Changed field name from matchresultatListaJSON
            {
                "match_id": match_id,  # Changed field name from matchid
                "result_type": 1,      # Changed field name from matchresultattypid
                "home_score": fulltime_home,  # Changed field name from matchlag1mal
                "away_score": fulltime_away,  # Changed field name from matchlag2mal
                "walkover": False,     # Changed field name from wo
                # Missing ow and ww fields
            },
            # ...
        ]
    }

    response_data = self._api_request(url, result_data_copy)
    return response_data
```

## Code Review Checklist for AI-Modified Code

When reviewing code that has been modified with AI assistance:

1. **Check for AI-Safe Markers**:
   - Verify that AI-safe markers are preserved
   - Ensure critical sections haven't been modified inappropriately

2. **Verify API Contracts**:
   - Confirm that API request and response structures are maintained
   - Check that field names and data types match API requirements

3. **Test API Interactions**:
   - Run tests that verify API interactions still work
   - Test both success and error cases

4. **Review Documentation**:
   - Ensure any changes are reflected in the documentation
   - Check that examples are updated if necessary

## Reporting Issues

If you encounter issues with AI-modified code:

1. Revert to the previous working version
2. Document the specific issue encountered
3. Create an issue in the issue tracker with details
4. Reference the AI-safe guidelines in your report

## Conclusion

By following these guidelines, we can leverage AI tools while maintaining the integrity of our API client. Remember that the primary goal is to ensure reliable communication with the FOGIS API, which requires strict adherence to API contracts.
