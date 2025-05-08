# Reduce Code Duplication in Integration Tests

## Description
The integration tests currently contain significant code duplication in the setup and teardown phases. Almost every test method contains identical code for setting up and restoring base URLs. This makes the tests harder to maintain and increases the risk of inconsistencies.

## Proposed Solution
Create a pytest fixture to handle the API URL overrides, as suggested in the PR review for #160:

```python
@pytest.fixture
def mock_api_urls(mock_fogis_server):
    """Temporarily override API URLs to point to mock server."""
    original_base_url = FogisApiClient.BASE_URL
    original_internal_base_url = InternalApiClient.BASE_URL
    
    FogisApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"
    InternalApiClient.BASE_URL = f"{mock_fogis_server['base_url']}/mdk"
    
    yield
    
    # Restore original URLs
    FogisApiClient.BASE_URL = original_base_url
    InternalApiClient.BASE_URL = original_internal_base_url
```

This fixture would:
1. Temporarily override the API URLs to point to the mock server
2. Yield control to the test
3. Restore the original URLs after the test completes

## Implementation Steps
1. Create the fixture in a common location (e.g., `integration_tests/conftest.py`)
2. Update all test methods to use the fixture instead of manually overriding URLs
3. Remove the duplicate code from all test methods
4. Run all tests to ensure they still pass
5. Update documentation to explain the fixture usage

## Benefits
- Reduces code duplication
- Makes tests more maintainable
- Ensures consistent URL handling across all tests
- Reduces the risk of forgetting to restore URLs
- Makes it easier to add new tests in the future

## Related Issues
- Part of the follow-up work for PR #160
- Addresses feedback from the PR review

## References
- [CONTRIBUTING.md](https://github.com/PitchConnect/fogis-api-client-python/blob/develop/CONTRIBUTING.md) - See sections on Testing and GitFlow Process
- [PR #160](https://github.com/PitchConnect/fogis-api-client-python/pull/160) - Original PR implementing comprehensive integration testing
