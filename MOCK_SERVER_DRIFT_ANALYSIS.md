# Mock Server Drift Analysis Report

**Date:** 2025-10-08
**Repository:** fogis-api-client-python
**Branch:** feat/containerized-mock-server
**Analysis Type:** Comprehensive Authentication & API Drift Analysis

---

## Executive Summary

This report documents the comprehensive analysis of drift between the FOGIS API mock server and the real client implementation, with a focus on authentication changes introduced in commit `1beb1db` (OAuth 2.0 PKCE Authentication Implementation).

### Key Findings

1. **🔴 CRITICAL: OAuth 2.0 PKCE Flow Not Fully Implemented in Mock Server**
   - Real client detects OAuth redirect by checking for `auth.fogis.se` in response URL
   - Mock server has basic OAuth endpoints but doesn't simulate the full redirect flow
   - Mock server doesn't redirect to OAuth when `/mdk/Login.aspx` is accessed

2. **⚠️ Authentication Flow Mismatch**
   - Real client: Checks for OAuth redirect → Falls back to ASP.NET if no redirect
   - Mock server: Only implements ASP.NET form authentication on login page
   - Missing: OAuth redirect simulation from login page

3. **✅ OAuth Endpoints Present But Incomplete**
   - Mock server has `/oauth/authorize`, `/oauth/callback`, `/oauth/token` endpoints
   - These endpoints are never reached because login page doesn't redirect to them
   - Token exchange endpoint returns mock tokens but isn't integrated with login flow

---

## 1. Authentication Changes in Real Client

### 1.1 OAuth 2.0 PKCE Implementation (Commit 1beb1db)

The real client now implements a **hybrid authentication flow**:

#### Flow Detection Logic
```python
# From fogis_api_client/internal/auth.py:69-81
response = session.get(login_url, timeout=(10, 30), allow_redirects=True)

# Check if we were redirected to OAuth
if "auth.fogis.se" in response.url:
    logger.info("Detected OAuth redirect - using OAuth 2.0 PKCE flow")
    return _handle_oauth_authentication(session, username, password, response.url)
else:
    logger.info("No OAuth redirect detected - using ASP.NET form authentication")
    return _handle_aspnet_authentication(session, username, password, response, login_url)
```

#### OAuth Authentication Components

1. **FogisOAuthManager** (`fogis_api_client/internal/fogis_oauth_manager.py`)
   - PKCE code challenge generation (RFC 7636 compliant)
   - OAuth endpoints:
     - Authorization: `https://auth.fogis.se/connect/authorize`
     - Token: `https://auth.fogis.se/connect/token`
   - Client ID: `fogis.mobildomarklient`
   - Redirect URI: `https://fogis.svenskfotboll.se/mdk/signin-oidc`
   - Scopes: `openid fogis profile anvandare personid offline_access`

2. **OAuth Login Form Handling**
   - Extracts form data from OAuth login page at `auth.fogis.se`
   - Submits credentials to OAuth provider
   - Waits for redirect back to `fogis.svenskfotboll.se`
   - Extracts ASP.NET session cookies from OAuth session (hybrid approach)

3. **Token Management**
   - Access token stored and used in `Authorization: Bearer {token}` header
   - Refresh token support for token renewal
   - Token expiration tracking

#### ASP.NET Fallback
- Still supports traditional ASP.NET form authentication
- Used when no OAuth redirect is detected
- Maintains backward compatibility

### 1.2 Authentication Methods Supported

The real client now supports **three authentication methods**:

1. **OAuth 2.0 PKCE** (Primary)
   - Full OAuth flow with PKCE
   - Returns OAuth tokens
   - Sets `Authorization: Bearer` header

2. **OAuth Hybrid** (Common)
   - OAuth login flow
   - Returns ASP.NET session cookies
   - Used for API calls (FOGIS-specific behavior)

3. **ASP.NET Form Authentication** (Fallback)
   - Traditional form-based login
   - Returns ASP.NET cookies
   - Legacy support

---

## 2. Mock Server Current Implementation

### 2.1 Login Endpoint (`/mdk/Login.aspx`)

**Current Behavior:**
```python
# From integration_tests/mock_fogis_server.py:119-138
@self.app.route("/mdk/Login.aspx", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Validates credentials
        # Sets ASP.NET cookies
        # Returns 302 redirect to /mdk/
    else:
        # Returns HTML login form (ASP.NET style)
```

**Issues:**
- ❌ GET request returns ASP.NET form, not OAuth redirect
- ❌ No detection of OAuth vs ASP.NET mode
- ❌ Doesn't redirect to `auth.fogis.se` domain
- ✅ POST request correctly validates credentials
- ✅ Sets correct ASP.NET cookies

### 2.2 OAuth Endpoints

**Current Implementation:**
```python
# From integration_tests/mock_fogis_server.py:964-1013
@self.app.route("/oauth/authorize", methods=["GET"])
def oauth_authorize():
    # Returns HTML with JavaScript redirect to /oauth/callback

@self.app.route("/oauth/callback", methods=["GET"])
def oauth_callback():
    # Returns HTML with JavaScript redirect to /mdk/

@self.app.route("/oauth/token", methods=["POST"])
def oauth_token():
    # Returns mock OAuth tokens
```

**Issues:**
- ❌ OAuth endpoints exist but are never reached
- ❌ No integration with login flow
- ❌ Doesn't simulate `auth.fogis.se` domain
- ❌ No PKCE parameter validation
- ❌ No state/nonce validation
- ✅ Token format is correct

### 2.3 Authentication Check

**Current Implementation:**
```python
# From integration_tests/mock_fogis_server.py:746-757
def _check_auth(self):
    if session.get("authenticated") or request.cookies.get("FogisMobilDomarKlient.ASPXAUTH"):
        return True
    return Response("Unauthorized", status=401)
```

**Issues:**
- ❌ Doesn't check for `Authorization: Bearer` header
- ❌ No OAuth token validation
- ✅ Correctly checks ASP.NET cookies

---

## 3. Comprehensive Drift Analysis

### 3.1 Authentication Drift

| Aspect | Real Client | Mock Server | Status |
|--------|-------------|-------------|--------|
| OAuth redirect detection | ✅ Checks for `auth.fogis.se` | ❌ Not implemented | 🔴 CRITICAL |
| OAuth login flow | ✅ Full PKCE flow | ❌ Endpoints exist but not integrated | 🔴 CRITICAL |
| OAuth token support | ✅ Bearer token in header | ❌ Not validated | 🔴 CRITICAL |
| ASP.NET form auth | ✅ Fallback support | ✅ Implemented | ✅ OK |
| Cookie authentication | ✅ Supported | ✅ Supported | ✅ OK |
| Hybrid OAuth+ASP.NET | ✅ Supported | ❌ Not implemented | 🔴 CRITICAL |
| Token refresh | ✅ Implemented | ❌ Not implemented | 🟡 MEDIUM |

### 3.2 API Endpoints Drift

Based on `API_CLIENT_MOCK_COMPARISON_REPORT.md`:

| Category | Status | Details |
|----------|--------|---------|
| Core read endpoints | ✅ Synchronized | Match list, details, players, officials, events, results |
| Write endpoints | ⚠️ Partial | Mock has more write endpoints than client uses |
| Legacy endpoints | 🟡 Extra in mock | Mock has deprecated endpoints not used by client |
| Convenience methods | ✅ OK | Client-side aggregation, no endpoints needed |

### 3.3 Request/Response Format Drift

| Aspect | Real Client | Mock Server | Status |
|--------|-------------|-------------|--------|
| JSON wrapping | `{"d": json.dumps(data)}` | `{"d": json.dumps(data)}` | ✅ OK |
| Match list format | `matchlista` field | `matchlista` field | ✅ OK |
| Error responses | JSON with `success: false` | JSON with `success: false` | ✅ OK |
| HTTP status codes | 401 for unauth, 400 for validation | Same | ✅ OK |

### 3.4 Headers Drift

| Header | Real Client | Mock Server | Status |
|--------|-------------|-------------|--------|
| `Authorization` | `Bearer {token}` for OAuth | ❌ Not checked | 🔴 CRITICAL |
| `User-Agent` | Browser-like UA string | ❌ Not validated | 🟢 OK (not critical) |
| `Content-Type` | `application/json` for API calls | ✅ Handled | ✅ OK |
| `Accept` | Various | ❌ Not validated | 🟢 OK (not critical) |

### 3.5 Session Management Drift

| Aspect | Real Client | Mock Server | Status |
|--------|-------------|-------------|--------|
| Cookie names | `FogisMobilDomarKlient.ASPXAUTH` | Same | ✅ OK |
| Session tracking | Via cookies or OAuth tokens | Only cookies | 🔴 CRITICAL |
| Token expiration | Tracked and refreshed | ❌ Not implemented | 🟡 MEDIUM |

### 3.6 Error Handling Drift

| Error Type | Real Client | Mock Server | Status |
|------------|-------------|-------------|--------|
| `FogisLoginError` | Raised on auth failure | Returns 401 or error page | ✅ Compatible |
| `FogisOAuthAuthenticationError` | OAuth-specific errors | ❌ Not implemented | 🔴 CRITICAL |
| `FogisAPIRequestError` | API call failures | Returns 400 with error | ✅ Compatible |
| Network errors | Proper exception handling | Flask default handling | ✅ OK |

---

## 4. Impact Assessment

### 4.1 Critical Issues (Must Fix)

1. **OAuth Redirect Not Simulated**
   - **Impact:** Tests using mock server don't exercise OAuth code path
   - **Risk:** OAuth bugs won't be caught in integration tests
   - **Affected:** All authentication tests

2. **Bearer Token Not Validated**
   - **Impact:** OAuth-authenticated requests not properly tested
   - **Risk:** Authorization header issues won't be detected
   - **Affected:** All API endpoint tests with OAuth

3. **Hybrid Authentication Not Supported**
   - **Impact:** Most common real-world auth flow not tested
   - **Risk:** Production issues with OAuth→ASP.NET cookie flow
   - **Affected:** Integration tests

### 4.2 Medium Priority Issues

1. **Token Refresh Not Implemented**
   - **Impact:** Long-running session tests not possible
   - **Risk:** Token expiration handling not tested

2. **OAuth Parameter Validation Missing**
   - **Impact:** Invalid OAuth requests not caught
   - **Risk:** PKCE implementation bugs not detected

### 4.3 Low Priority Issues

1. **Extra Write Endpoints in Mock**
   - **Impact:** None (extra functionality)
   - **Action:** Document or remove if not needed

2. **Legacy Endpoints in Mock**
   - **Impact:** None (backward compatibility)
   - **Action:** Keep for compatibility

---

## 5. Recommendations

### 5.1 Immediate Actions (Critical)

1. **Implement OAuth Redirect Simulation**
   - Modify `/mdk/Login.aspx` GET to redirect to mock OAuth provider
   - Use environment variable or config to enable/disable OAuth mode
   - Simulate `auth.fogis.se` domain behavior

2. **Add Bearer Token Validation**
   - Update `_check_auth()` to check `Authorization` header
   - Validate mock OAuth tokens
   - Support both cookie and token authentication

3. **Implement Hybrid Authentication Flow**
   - OAuth login returns ASP.NET cookies
   - Match real FOGIS behavior

### 5.2 Medium Priority Actions

1. **Add Token Refresh Endpoint**
   - Implement `/oauth/token` refresh grant
   - Track token expiration
   - Return new tokens

2. **Add OAuth Parameter Validation**
   - Validate PKCE parameters
   - Check state and nonce
   - Return proper OAuth errors

### 5.3 Long-term Improvements

1. **Configuration System**
   - Allow switching between OAuth and ASP.NET modes
   - Support different authentication scenarios
   - Enable/disable specific features

2. **Enhanced Logging**
   - Log authentication attempts
   - Track OAuth flow steps
   - Aid debugging

3. **Documentation**
   - Document authentication modes
   - Provide examples for each flow
   - Update integration test docs

---

## 6. Proposed Changes

See implementation in the following files:
- `integration_tests/mock_fogis_server.py` - Updated authentication flow
- `integration_tests/test_with_mock_server.py` - Updated tests
- `docs/mock_server.md` - Updated documentation

---

## 7. Testing Strategy

### 7.1 Test OAuth Flow
- Test OAuth redirect detection
- Test OAuth login form submission
- Test token exchange
- Test Bearer token authentication

### 7.2 Test ASP.NET Fallback
- Test ASP.NET form authentication
- Test cookie-based authentication
- Test backward compatibility

### 7.3 Test Hybrid Flow
- Test OAuth login with ASP.NET cookies
- Test API calls with hybrid auth
- Test session management

---

## Conclusion

The mock server requires significant updates to match the real client's OAuth 2.0 PKCE authentication implementation. The current mock server only supports ASP.NET form authentication, while the real client primarily uses OAuth with ASP.NET cookies as a hybrid approach. This drift creates a critical gap in integration testing coverage.

**Priority:** 🔴 **HIGH** - Authentication is fundamental to all API operations
**Effort:** ~4-6 hours of development + testing
**Risk if not fixed:** OAuth-related bugs will not be caught in integration tests, leading to potential production issues
