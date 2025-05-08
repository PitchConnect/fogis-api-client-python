# Implement Parameterized Tests for Similar Test Cases

## Description
The current integration tests contain several similar test cases with different inputs (like various match result scenarios). Using pytest's parameterization could further reduce code duplication and make it easier to add new test cases in the future.

## Proposed Solution
Refactor similar test cases to use pytest's parameterization features:

```python
@pytest.mark.parametrize(
    "scenario,home_score,away_score,expected_result",
    [
        ("normal", 2, 1, True),
        ("draw", 1, 1, True),
        ("away_win", 0, 3, True),
        ("invalid_score", -1, 0, False),
    ],
)
def test_report_match_result_scenarios(
    self, mock_fogis_server, mock_api_urls, test_credentials, 
    scenario, home_score, away_score, expected_result
):
    """Test reporting match results with various scenarios."""
    # Test setup...
    
    result_data = {
        "match_id": 12345,
        "home_score": home_score,
        "away_score": away_score,
        # Other fields...
    }
    
    if expected_result:
        response = client.report_match_result(result_data)
        assert isinstance(response, dict)
        assert "success" in response
        assert response["success"] is True
    else:
        with pytest.raises(ValueError):
            client.report_match_result(result_data)
```

## Implementation Steps
1. Identify groups of similar test cases that could be parameterized
2. Refactor these tests to use pytest's parameterization
3. Add additional test cases to cover more scenarios
4. Run all tests to ensure they still pass
5. Update documentation to explain the parameterized tests

## Benefits
- Further reduces code duplication
- Makes it easier to add new test cases
- Improves test coverage by encouraging more test scenarios
- Makes the test suite more maintainable
- Provides clearer documentation of test scenarios

## Related Issues
- Part of the follow-up work for PR #160
- Addresses feedback from the PR review

## References
- [CONTRIBUTING.md](https://github.com/PitchConnect/fogis-api-client-python/blob/develop/CONTRIBUTING.md) - See sections on Testing and Test Structure
- [PR #160](https://github.com/PitchConnect/fogis-api-client-python/pull/160) - Original PR implementing comprehensive integration testing
- [pytest documentation on parameterization](https://docs.pytest.org/en/stable/how-to/parametrize.html)
