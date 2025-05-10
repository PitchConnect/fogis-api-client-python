# FOGIS API Client Architecture

This document provides an overview of the FOGIS API Client architecture, including system components, data flow, and integration points.

> **Note:** For detailed information about the API architecture, including the separation between public and internal APIs, adapter patterns, and best practices, see the [API Architecture Documentation](api_architecture.md).

## System Components

The FOGIS API Client consists of several key components that work together to provide a seamless interface to the FOGIS API:

```
┌─────────────────────────────────────────────────────────────────┐
│                     FOGIS API Client Library                     │
├─────────────┬─────────────┬────────────────┬───────────────────┤
│ FogisApiClient │ Event Types │ Type Definitions │ Exception Handling │
└─────────────┴─────────────┴────────────────┴───────────────────┘
                │                  │                  │
                ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Request Layer                        │
├─────────────────────────────────────────────────────────────────┤
│                        Session Management                        │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                           FOGIS API                              │
│                  (Svenska Fotbollförbundet API)                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1. FogisApiClient Class

The core component of the library is the `FogisApiClient` class, which provides methods for:

- Authentication and session management
- Fetching match data
- Reporting match events and results
- Managing team and player information

### 2. Event Types

The `EVENT_TYPES` dictionary defines the various types of events that can be reported in a match, including:

- Goals (regular, header, corner, free kick, own goal, penalty)
- Cards (yellow, red)
- Substitutions
- Control events (period start/end, match end)

### 3. Type Definitions

The library includes TypedDict classes that define the structure of data returned by the API:

- `MatchDict`: Match information
- `PlayerDict`: Player information
- `OfficialDict`: Official information
- `EventDict`: Event information
- `MatchResultDict`: Match result information

### 4. Exception Handling

Custom exception classes provide specific error handling for different types of failures:

- `FogisLoginError`: Authentication failures
- `FogisAPIRequestError`: API request failures
- `FogisDataError`: Data parsing or validation failures

### 5. HTTP Request Layer

The library uses the `requests` library to handle HTTP communication with the FOGIS API, including:

- Making POST and GET requests
- Handling cookies and session management
- Processing JSON responses

## Data Flow

The following diagram illustrates the data flow between the client application, the FOGIS API Client library, and the FOGIS API:

```
┌─────────────────┐      ┌─────────────────────────────────────┐      ┌─────────────────┐
│                 │      │                                     │      │                 │
│  Client         │      │  FOGIS API Client Library           │      │  FOGIS API      │
│  Application    │ ──►  │                                     │ ──►  │  Server         │
│                 │      │                                     │      │                 │
└─────────────────┘      └─────────────────────────────────────┘      └─────────────────┘
        ▲                                  ▲                                  │
        │                                  │                                  │
        └──────────────────────────────────┴──────────────────────────────────┘
                                Data Flow
```

### Authentication Flow

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Application │     │ FogisApiClient  │     │ FOGIS API       │
└─────┬───────┘     └────────┬────────┘     └────────┬────────┘
      │                      │                       │
      │ Initialize           │                       │
      │ with credentials     │                       │
      │─────────────────────►│                       │
      │                      │                       │
      │                      │ Login request         │
      │                      │───────────────────────►
      │                      │                       │
      │                      │ Session cookies       │
      │                      │◄───────────────────────
      │                      │                       │
      │ API request          │                       │
      │─────────────────────►│                       │
      │                      │ Authenticated request │
      │                      │───────────────────────►
      │                      │                       │
      │                      │ Response data         │
      │                      │◄───────────────────────
      │ Processed data       │                       │
      │◄─────────────────────│                       │
      │                      │                       │
```

### Match Reporting Flow

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ Application │     │ FogisApiClient  │     │ FOGIS API       │
└─────┬───────┘     └────────┬────────┘     └────────┬────────┘
      │                      │                       │
      │ Fetch match          │                       │
      │─────────────────────►│                       │
      │                      │ Get match request     │
      │                      │───────────────────────►
      │                      │                       │
      │                      │ Match data            │
      │                      │◄───────────────────────
      │ Match data           │                       │
      │◄─────────────────────│                       │
      │                      │                       │
      │ Report event         │                       │
      │─────────────────────►│                       │
      │                      │ Post event request    │
      │                      │───────────────────────►
      │                      │                       │
      │                      │ Event response        │
      │                      │◄───────────────────────
      │ Event confirmation   │                       │
      │◄─────────────────────│                       │
      │                      │                       │
      │ Report result        │                       │
      │─────────────────────►│                       │
      │                      │ Post result request   │
      │                      │───────────────────────►
      │                      │                       │
      │                      │ Result response       │
      │                      │◄───────────────────────
      │ Result confirmation  │                       │
      │◄─────────────────────│                       │
      │                      │                       │
      │ Mark as finished     │                       │
      │─────────────────────►│                       │
      │                      │ Finish request        │
      │                      │───────────────────────►
      │                      │                       │
      │                      │ Finish response       │
      │                      │◄───────────────────────
      │ Finish confirmation  │                       │
      │◄─────────────────────│                       │
      │                      │                       │
```

## Integration Points

The FOGIS API Client can be integrated with various systems and applications:

### 1. Web Applications

The client can be used in web applications to provide FOGIS functionality:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Web Server     │ ──►  │  FOGIS API      │ ──►  │  FOGIS API      │
│  (Flask/Django) │      │  Client         │      │  Server         │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        ▲                                                  │
        │                                                  │
        ▼                                                  ▼
┌─────────────────┐                              ┌─────────────────┐
│                 │                              │                 │
│  Web Browser    │                              │  FOGIS Database │
│                 │                              │                 │
└─────────────────┘                              └─────────────────┘
```

### 2. Mobile Applications

The client can be used in the backend of mobile applications:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Mobile App     │ ──►  │  Backend API    │ ──►  │  FOGIS API      │
│  (iOS/Android)  │      │  with FOGIS     │      │  Server         │
│                 │      │  Client         │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### 3. Command-Line Tools

The client can be used in command-line tools for match reporting and data retrieval:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  CLI Tool       │ ──►  │  FOGIS API      │ ──►  │  FOGIS API      │
│                 │      │  Client         │      │  Server         │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### 4. Automated Systems

The client can be used in automated systems for data synchronization:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Scheduled      │ ──►  │  FOGIS API      │ ──►  │  FOGIS API      │
│  Tasks          │      │  Client         │      │  Server         │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                                                  │
        │                                                  │
        ▼                                                  ▼
┌─────────────────┐                              ┌─────────────────┐
│                 │                              │                 │
│  Local Database │                              │  FOGIS Database │
│                 │                              │                 │
└─────────────────┘                              └─────────────────┘
```

## Security Considerations

The FOGIS API Client implements several security features:

1. **Cookie-Based Authentication**: The client supports cookie-based authentication, which is more secure than storing credentials.

2. **Lazy Login**: The client implements lazy login, only authenticating when needed.

3. **Session Validation**: The client can validate if a session is still valid before making requests.

4. **Error Handling**: The client provides detailed error messages for security-related issues.

5. **No Credential Storage**: The client does not store credentials internally after authentication.

## Performance Considerations

The FOGIS API Client is designed with performance in mind:

1. **Session Reuse**: The client reuses the same session for multiple requests to reduce overhead.

2. **Lazy Loading**: The client only fetches data when needed.

3. **Efficient JSON Parsing**: The client efficiently parses JSON responses.

4. **Minimal Dependencies**: The client has minimal dependencies to reduce overhead.

## Future Enhancements

Potential future enhancements to the architecture include:

1. **Asynchronous Support**: Adding support for asynchronous requests using `aiohttp` or similar libraries.

2. **Caching Layer**: Implementing a caching layer to reduce API calls for frequently accessed data.

3. **Rate Limiting**: Adding built-in rate limiting to prevent API abuse.

4. **Webhook Support**: Adding support for webhooks to receive real-time updates from FOGIS.

5. **Offline Mode**: Implementing an offline mode for working without an internet connection.
