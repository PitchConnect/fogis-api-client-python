# API Client & Mock Server Synchronization Action Plan

**Date:** 2025-10-05
**Status:** 🔴 **ACTION REQUIRED**

---

## Quick Summary

The comparison between `fogis_api_client/public_api_client.py` and `integration_tests/mock_fogis_server.py` revealed:

- ✅ **Read operations:** Well synchronized
- ❌ **Write operations:** 7 critical endpoints missing from client
- ⚠️ **Response formats:** 2 minor inconsistencies
- ⚠️ **Validation:** Incomplete coverage in mock

---

## Critical Issues Requiring Immediate Attention

### Issue #1: Missing Write Operation Methods 🔴 CRITICAL

**Problem:** The mock server implements 7 write/mutation endpoints that are NOT exposed in the public API client.

**Missing Endpoints:**

| Endpoint | Purpose | Mock Line |
|----------|---------|-----------|
| `SparaMatchhandelse` | Save match event | 319, 559 |
| `RaderaMatchhandelse` | Delete match event | 569 |
| `SparaMatchresultatLista` | Report match result | 602 |
| `SparaMatchGodkannDomarrapport` | Mark reporting finished | 358, 592 |
| `SparaMatchdeltagare` | Save match participant | 624 |
| `SparaMatchlagledare` | Save team official | 676 |
| `RensaMatchhandelser` | Clear match events | 341 |

**Impact:**
- API client is **read-only**
- Cannot perform referee reporting workflows
- Cannot save match results or events
- Integration tests may be testing functionality that doesn't exist in the client

**Recommended Actions:**

**Option A: Implement Missing Methods (Recommended if these are needed)**

Add the following methods to `fogis_api_client/public_api_client.py`:

```python
def save_match_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save a match event."""
    url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchhandelse"
    response = self._make_authenticated_request("POST", url, json=event_data)
    # Parse and return response

def delete_match_event(self, event_id: Union[int, str]) -> Dict[str, Any]:
    """Delete a match event."""
    url = f"{self.BASE_URL}/MatchWebMetoder.aspx/RaderaMatchhandelse"
    payload = {"matchhandelseid": int(event_id)}
    response = self._make_authenticated_request("POST", url, json=payload)
    # Parse and return response

def report_match_result(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
    """Report match result."""
    url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchresultatLista"
    response = self._make_authenticated_request("POST", url, json=result_data)
    # Parse and return response

def mark_reporting_finished(self, match_id: Union[int, str]) -> Dict[str, Any]:
    """Mark match reporting as finished."""
    url = f"{self.BASE_URL}/Fogis/Match/SparaMatchGodkannDomarrapport"
    payload = {"matchid": int(match_id)}
    response = self._make_authenticated_request("POST", url, json=payload)
    # Parse and return response

def save_match_participant(self, participant_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save match participant data."""
    url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchdeltagare"
    response = self._make_authenticated_request("POST", url, json=participant_data)
    # Parse and return response

def save_team_official(self, official_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save team official data."""
    url = f"{self.BASE_URL}/MatchWebMetoder.aspx/SparaMatchlagledare"
    response = self._make_authenticated_request("POST", url, json=official_data)
    # Parse and return response

def clear_match_events(self, match_id: Union[int, str]) -> Dict[str, Any]:
    """Clear all events for a match."""
    url = f"{self.BASE_URL}/MatchWebMetoder.aspx/RensaMatchhandelser"
    payload = {"matchid": int(match_id)}
    response = self._make_authenticated_request("POST", url, json=payload)
    # Parse and return response
```

**Option B: Document Intentional Exclusion**

If these endpoints are intentionally not exposed (e.g., internal-only or deprecated):

1. Add comments in the mock server explaining why these exist
2. Update documentation to clarify the client is read-only
3. Consider moving these endpoints to a separate "internal" mock server

**Estimated Effort:** 4-6 hours (Option A) or 1 hour (Option B)

---

### Issue #2: Response Format Inconsistencies ⚠️ MEDIUM

**Problem:** Some mock endpoints return direct data while others return JSON strings, creating inconsistency.

**Specific Cases:**

1. **Match Result Endpoint** (`GetMatchresultatlista`)
   - **Client expects:** Both `{"d": json_string}` and `{"d": direct_dict}`
   - **Mock returns:** `{"d": direct_dict}` (line 316)
   - **Recommendation:** Change mock to return `{"d": json.dumps(result_data)}`

2. **Match Events Endpoints**
   - **Legacy endpoint** (`HamtaMatchHandelser`, line 297): Returns `{"d": events_data}` (direct)
   - **New endpoint** (`GetMatchhandelselista`, line 506): Returns `{"d": json.dumps(events_data)}` (string)
   - **Recommendation:** Standardize both to use JSON string format

**Code Changes Required:**

```python
# File: integration_tests/mock_fogis_server.py

# Line 316 - Change from:
return jsonify({"d": result_data})
# To:
return jsonify({"d": json.dumps(result_data)})

# Line 297 - Change from:
return jsonify({"d": events_data})
# To:
return jsonify({"d": json.dumps(events_data)})
```

**Estimated Effort:** 30 minutes

---

### Issue #3: Incomplete Validation Coverage ⚠️ MEDIUM

**Problem:** Only 7 out of 20+ endpoints have request validation enabled in the mock server.

**Endpoints WITH validation:**
- `SparaMatchhandelse`
- `GetMatchdeltagareLista`
- `GetMatchfunktionarerLista`
- `GetMatchresultatlista`
- `RaderaMatchhandelse`
- `SparaMatchresultatLista`
- `SparaMatchlagledare`

**Endpoints WITHOUT validation:**
- `GetMatcherAttRapportera` ⚠️
- `GetMatchdeltagareListaForMatchlag` ⚠️
- `GetMatchlagledareListaForMatchlag` ⚠️
- `GetMatchhandelselista` ⚠️
- And others...

**Recommendation:**

Add validation to all endpoints or document why certain endpoints skip validation:

```python
# Add to each endpoint handler:
endpoint = "/MatchWebMetoder.aspx/GetMatcherAttRapportera"
is_valid, error_msg = self._validate_and_log_request(endpoint, data)
if not is_valid:
    return jsonify({"d": json.dumps({"success": False, "error": error_msg})}), 400
```

**Estimated Effort:** 2-3 hours

---

## Minor Issues

### Issue #4: Duplicate/Legacy Endpoints 🟡 LOW

**Problem:** Mock server has multiple versions of the same endpoint (legacy + new).

**Examples:**
- `HamtaMatchLista` vs `GetMatcherAttRapportera`
- `HamtaMatch` vs `GetMatch`
- `HamtaMatchSpelare` vs `GetMatchdeltagareLista`

**Recommendation:**
1. Add comments marking legacy endpoints
2. Consider deprecation warnings in mock responses
3. Document which endpoints are current vs legacy

**Estimated Effort:** 1 hour

---

### Issue #5: Missing Header Validation 🟡 LOW

**Problem:** Mock server doesn't validate request headers.

**Client sends:**
```python
{
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Origin": "https://fogis.svenskfotboll.se",
    "Referer": f"{self.BASE_URL}/",
    "X-Requested-With": "XMLHttpRequest",
}
```

**Recommendation:** Add header validation to mock for more realistic testing.

**Estimated Effort:** 1-2 hours

---

## Prioritized Action Plan

### Phase 1: Critical Fixes (Week 1)

**Priority 1.1: Decide on Write Operations** ⏱️ 1 day
- [ ] Review whether write operations should be in public API
- [ ] If yes, implement methods (Issue #1, Option A)
- [ ] If no, document exclusion (Issue #1, Option B)
- [ ] Update tests accordingly

**Priority 1.2: Fix Response Format Inconsistencies** ⏱️ 2 hours
- [ ] Standardize match result response format (Issue #2)
- [ ] Standardize match events response format (Issue #2)
- [ ] Test all affected endpoints
- [ ] Update integration tests if needed

### Phase 2: Important Improvements (Week 2)

**Priority 2.1: Add Validation Coverage** ⏱️ 1 day
- [ ] Add validation to all core endpoints (Issue #3)
- [ ] Document validation rules
- [ ] Add tests for validation errors

**Priority 2.2: Clean Up Legacy Endpoints** ⏱️ 4 hours
- [ ] Mark legacy endpoints with comments (Issue #4)
- [ ] Document endpoint versions
- [ ] Consider deprecation strategy

### Phase 3: Nice to Have (Week 3)

**Priority 3.1: Add Header Validation** ⏱️ 4 hours
- [ ] Implement header validation in mock (Issue #5)
- [ ] Add tests for header validation

**Priority 3.2: Documentation** ⏱️ 4 hours
- [ ] Create endpoint mapping document
- [ ] Document request/response schemas
- [ ] Update API documentation

---

## Testing Checklist

After implementing fixes, verify:

- [ ] All client methods have corresponding mock endpoints
- [ ] All mock endpoints are used by client (or documented as unused)
- [ ] Response formats are consistent across all endpoints
- [ ] Request validation works for all endpoints
- [ ] Integration tests pass
- [ ] Unit tests pass
- [ ] Documentation is updated

---

## Files to Modify

### Primary Files:
1. `fogis_api_client/public_api_client.py` - Add write operation methods
2. `integration_tests/mock_fogis_server.py` - Fix response formats, add validation

### Documentation Files:
3. `docs/api_reference.md` - Document new methods
4. `README.md` - Update feature list
5. `CHANGELOG.md` - Document changes

### Test Files:
6. `tests/test_public_api_client.py` - Add tests for new methods
7. `integration_tests/test_api_endpoints.py` - Update integration tests

---

## Success Criteria

✅ **Synchronization Complete When:**

1. All write operations are either implemented or documented as excluded
2. Response formats are consistent across all endpoints
3. All endpoints have validation (or documented exceptions)
4. All integration tests pass
5. Documentation is updated
6. No critical discrepancies remain

---

## Questions to Answer

Before proceeding, clarify:

1. **Are write operations intentionally excluded from the public API?**
   - If yes, why? (Security, stability, etc.)
   - If no, when should they be implemented?

2. **What is the actual FOGIS API response format?**
   - Does it return JSON strings or direct objects in the "d" field?
   - This will determine which format is correct

3. **Should legacy endpoints be removed from the mock?**
   - Or should they be maintained for backward compatibility?

4. **What is the validation strategy?**
   - Should all endpoints validate requests?
   - Or only write operations?

---

## Contact & Next Steps

**Prepared by:** Augment Code AI Assistant
**Date:** 2025-10-05

**Next Steps:**
1. Review this action plan
2. Answer the questions above
3. Prioritize which issues to address first
4. Begin implementation following the phased approach

**For Questions:**
- Review the detailed comparison report: `API_CLIENT_MOCK_COMPARISON_REPORT.md`
- Check specific line numbers referenced in this document
- Run integration tests to see current behavior

---

**Status:** 🔴 Awaiting decision on write operations (Issue #1)
