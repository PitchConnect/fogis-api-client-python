# Enhance Error Assertions and Test Isolation in Integration Tests

## Description
The current integration tests cover error cases but could benefit from more specific assertions about error messages to ensure they're informative for developers. Additionally, the use of `clear-request-history` is not consistently applied across all tests, which could lead to test isolation issues.

## Proposed Solutions

### 1. Enhanced Error Assertions
Add more specific assertions about error messages in tests that handle error cases:
- Verify that error messages contain specific information about what went wrong
- Check for specific error codes or types
- Ensure error messages are helpful for debugging

Example:
```python
# Current assertion
with pytest.raises(FogisAPIRequestError):
    client.report_match_result(result_data)

# Enhanced assertion
with pytest.raises(FogisAPIRequestError) as excinfo:
    client.report_match_result(result_data)
assert "Missing required field" in str(excinfo.value)
assert "match_id" in str(excinfo.value)
```

### 2. Consistent Test Isolation
Apply the `clear-request-history` pattern consistently across all tests:
- Add a call to clear request history at the beginning of each test
- Consider adding this to the fixture setup
- Ensure each test runs in isolation without being affected by previous tests

Example:
```python
def test_something(mock_fogis_server, mock_api_urls):
    # Clear request history at the beginning of the test
    requests.get(f"{mock_fogis_server['base_url']}/clear-request-history")
    
    # Test code...
```

## Implementation Steps
1. Identify all tests that handle error cases and enhance their assertions
2. Add request history clearing to all tests or to a common fixture
3. Run all tests to ensure they still pass
4. Update documentation to explain the enhanced error handling and test isolation

## Benefits
- More informative test failures
- Better test isolation
- Easier debugging of test failures
- More robust test suite
- Better documentation of expected error behavior

## Related Issues
- Part of the follow-up work for PR #160
- Addresses feedback from the PR review

## References
- [CONTRIBUTING.md](https://github.com/PitchConnect/fogis-api-client-python/blob/develop/CONTRIBUTING.md) - See sections on Testing and Test Structure
- [PR #160](https://github.com/PitchConnect/fogis-api-client-python/pull/160) - Original PR implementing comprehensive integration testing
