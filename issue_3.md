# Update Main README with Integration Testing Information

## Description
The main README.md file currently lacks information about the integration testing infrastructure implemented in PR #160. Adding a section about integration tests would help highlight this important safeguard for new contributors and provide guidance on how to use and extend the tests.

## Proposed Solution
Add a new section to the main README.md file that:
1. Explains the purpose and importance of integration tests
2. Provides instructions for running integration tests
3. Links to the more detailed documentation in the integration_tests directory
4. Explains how to add new tests for new features

## Example Content
```markdown
## Integration Testing

This project includes comprehensive integration tests to verify that the client correctly interacts with the FOGIS API. These tests use a mock server to simulate the API responses and validate the request structure.

### Running Integration Tests

Integration tests can be run in several ways:

#### Using Docker (Recommended)
```bash
./run_integration_tests.sh
```
This script sets up the necessary Docker containers and runs the tests in an isolated environment.

#### Running Locally
```bash
# Make sure you have the dependencies installed
pip install -e ".[dev]"

# Run the tests
python -m pytest integration_tests
```
Note: When running locally, the tests will automatically start a mock server if needed.

### Adding New Tests

When adding new features or modifying existing ones, please add or update the integration tests to ensure the client continues to work correctly with the API.

For more details, see the [integration tests documentation](integration_tests/README.md).
```

## Implementation Steps
1. Update the main README.md file with the new section
2. Ensure the information is accurate and consistent with the existing documentation
3. Add links to the more detailed documentation in the integration_tests directory
4. Update any related documentation as needed

## Benefits
- Increases visibility of the integration testing infrastructure
- Helps new contributors understand the testing requirements
- Provides clear guidance on how to run and extend the tests
- Encourages better test coverage for new features

## Related Issues
- Part of the follow-up work for PR #160
- Addresses feedback from the PR review
- Related to Issue #162 (Improve integration testing documentation)

## References
- [CONTRIBUTING.md](https://github.com/PitchConnect/fogis-api-client-python/blob/develop/CONTRIBUTING.md) - See sections on Testing and Documentation
- [PR #160](https://github.com/PitchConnect/fogis-api-client-python/pull/160) - Original PR implementing comprehensive integration testing
- [Issue #162](https://github.com/PitchConnect/fogis-api-client-python/issues/162) - Improve integration testing documentation
