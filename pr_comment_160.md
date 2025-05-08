Thank you for the detailed review! I've created the following issues to address your suggestions:

1. [Issue #163: Reduce Code Duplication in Integration Tests](https://github.com/PitchConnect/fogis-api-client-python/issues/163) - Create a pytest fixture to handle API URL overrides and reduce duplication in test setup/teardown.

2. [Issue #164: Enhance Error Assertions and Test Isolation in Integration Tests](https://github.com/PitchConnect/fogis-api-client-python/issues/164) - Add more specific assertions about error messages and apply the `clear-request-history` pattern consistently.

3. [Issue #165: Update Main README with Integration Testing Information](https://github.com/PitchConnect/fogis-api-client-python/issues/165) - Add a section about integration tests to the main README.md file.

4. [Issue #166: Implement Parameterized Tests for Similar Test Cases](https://github.com/PitchConnect/fogis-api-client-python/issues/166) - Refactor similar test cases to use pytest's parameterization features.

These issues follow the guidelines in [CONTRIBUTING.md](https://github.com/PitchConnect/fogis-api-client-python/blob/develop/CONTRIBUTING.md) and will help improve the integration testing infrastructure while keeping the current PR focused on the core implementation.

Would you like me to address any of these issues in this PR, or should we merge this PR as is and address these issues in follow-up PRs?
