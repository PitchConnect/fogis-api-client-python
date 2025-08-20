# FOGIS API Client Architecture

This document provides an overview of the FOGIS API Client architecture, including its main components and data flow.

## System Components

The FOGIS API Client has been simplified to a single, cohesive client that provides a direct interface to the FOGIS API. The complex separation between a "public" and "internal" API has been removed to improve developer experience and ease of maintenance.

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Application                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FogisApiClient                            │
│                                                                  │
│  • Provides methods for all FOGIS API endpoints.                 │
│  • Handles authentication and session management.                │
│  • Performs necessary data transformations internally.           │
│  • Raises specific exceptions for errors.                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          FOGIS Server                            │
└─────────────────────────────────────────────────────────────────┘
```

### 1. FogisApiClient Class

The core of the library is the `FogisApiClient` class, located in `fogis_api_client/fogis_api_client.py`. This single class is responsible for all interactions with the FOGIS API. Its responsibilities include:

-   **Authentication:** Handles login and session management via a `login()` method and automatic lazy login.
-   **API Requests:** Contains a private `_api_request` method that is the single entry point for all HTTP requests to the FOGIS server.
-   **Endpoint Methods:** Provides a public method for each FOGIS API endpoint (e.g., `fetch_match_json`, `report_match_result`).
-   **Data Handling:** Each endpoint method is responsible for constructing the correct request payload and parsing the response from the server.

### 2. Type Definitions

The library uses `TypedDict` classes to define the structure of data sent to and received from the API. These are located in `fogis_api_client/types.py`.

### 3. Exception Handling

The client uses a set of custom exceptions to signal different error conditions:

-   `FogisLoginError`: For authentication failures.
-   `FogisAPIRequestError`: For network or server-side API errors.
-   `FogisDataError`: For issues with the data returned by the API (e.g., unexpected format).

## Data Flow

The data flow is now much simpler. The user's application interacts directly with the `FogisApiClient`, which in turn communicates with the FOGIS server.

```
┌─────────────────┐      ┌────────────────────┐      ┌─────────────────┐
│                 │      │                    │      │                 │
│  Client         │      │  FogisApiClient    │      │  FOGIS API      │
│  Application    │ ──►  │                    │ ──►  │  Server         │
│                 │      │                    │      │                 │
└─────────────────┘      └────────────────────┘      └─────────────────┘
        ▲                        │                         │
        │                        │                         │
        └────────────────────────┴─────────────────────────┘
                       Data and Responses
```

This simplified architecture makes it much easier to add new features or debug existing ones, as all the logic for a given endpoint is contained within a single method in the `FogisApiClient`.
