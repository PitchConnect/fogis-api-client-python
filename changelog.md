# Changelog

## [0.3.0] - 2025-04-25

### Added
- Added more endpoints to the HTTP wrapper (Issue #118)

### Changed
- Optimized cookie validation to use a more lightweight approach (Issue #119)
- Organized tools into dedicated directories and improved documentation (Issue #122)
- Integrated dynamic pre-commit hook generator to keep local checks in sync with CI/CD (Issue #114)
- Improved setup experience with aligned pre-commit hooks (Issue #117)

### Removed
- Removed session management tools (moved to dedicated repository)

## [0.2.4] - 2025-04-17

### Fixed
- Corrected parameter names in team endpoints from "lagid" to "matchlagid" (Issue #101)

## [0.2.3] - 2025-04-17

### Fixed
- Fixed PyPI publishing workflow to use the correct API token format

## [0.2.2] - 2025-04-16

### Fixed
- Fixed all API endpoint URLs to use the correct paths
- Added comprehensive API endpoint documentation to prevent future issues
- Fixed fetch_matches_list_json method to use the correct endpoint and payload structure

## [0.2.1] - 2025-04-16

### Fixed
- Fixed login redirect URL handling to correctly process redirects after authentication
- Resolved 404 error caused by duplicate path segments in redirect URL

## [0.2.0] - 2025-04-16

### Added
- Mock FOGIS API server for integration tests (Issue #91)
  - Flask-based mock server that simulates all FOGIS API endpoints
  - Data factory that generates realistic sample data
  - Integration tests that use the mock server
  - Documentation for third-party integration testing
- Expanded guidelines in CONTRIBUTING.md for using markdown files with GitHub CLI
  - Added examples for PR descriptions, issue templates, and comments
  - Improved guidelines for AI agents contributing to the project

### Fixed
- Fixed login functionality to work with updated FOGIS login form
  - Updated authentication process to handle form changes
  - Improved error handling for login failures

## [0.1.0] - 2025-04-11

### Added
- Cookie-based authentication support (Issue #1)
  - Users can now authenticate using cookies instead of username/password
  - New `get_cookies()` method to retrieve session cookies for later use
  - New `validate_cookies()` method to check if cookies are still valid
- Flask endpoints for credential management (Issue #13)
  - `/auth/login`: Generate and return tokens based on credentials
  - `/auth/validate`: Check if a token is valid
  - `/auth/refresh`: Refresh an existing token
  - `/auth/logout`: Revoke a token
- Type hints throughout the codebase (Issue #51)
- Pre-commit hooks for code quality (Issue #54)
- Health check endpoint for Docker (Issue #46)
- Improved testing guidelines in CONTRIBUTING.md

### Changed
- Renamed HTTP wrapper to FOGIS API Gateway (Issue #30)
- Improved Docker configuration
- Reduced integration test wait time
- Updated documentation with examples of cookie-based authentication

### Fixed
- Fixed type conversion in API client to accept both string and integer IDs
- Fixed integration test wait time to exit early when API is ready

## [0.0.11] - 2025-04-11

### Changed
- Reverted to v0.0.5 codebase due to critical issues in later versions

## [0.0.10] - 2025-04-08

### Added
- Added the report_team_official_action method
- Fixed the CI/CD pipeline tests

## [0.0.9] - 2025-04-08

### Added
- Added tests for report_team_official_action method

## [0.0.8] - 2025-04-08

### Fixed
- Restored event_types dictionary that was accidentally removed

## [0.0.7] - 2025-04-08

### Fixed
- Ensure all IDs are handled as integers throughout the codebase

## [0.0.6] - 2025-04-08

### Added
- Implemented lazy login in FogisApiClient - now the client only logs in when needed, improving performance and reliability
- Added functionality to mark matches as done (mark_reporting_finished method)

### Improved
- Various improvements to the development environment (Docker setup, API Gateway, Swagger UI)
- Enhanced CI/CD pipeline and testing infrastructure

## [0.0.5] - 2025-03-14

### Fixed
- Completely revamped the entire filtering logic to use the `MatchListFilter` class for both server side and local filtering.

### Added
- `MatchListFilter` class for that passes a date filter to the API client and then does client-side filtering on the returned data.
- Filtering for status, age category, gender, and football type.

## [0.0.4] - 2025-03-05

### Added
- Added optional filter parameter for `fetch_matches_list_json`
- Added FilterBuilder class for creating filter parameters for `fetch_matches_list_json`
- Added `FogisFilterValidationError` exception class for handling invalid filter parameters.

## [0.0.3] - 2025-02-28

### Fixed
- Fixed file structure to allow proper installation and test execution.

## [0.0.2] - 2025-02-21

### Fixed
- Corrected package structure to allow proper installation and test execution.
- Added `pytest`, `pytest-mock`, `pytest-cov`, `flake8` as development dependencies.

### Added
- Changelog file to document releases.
