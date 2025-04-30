"""
Tests for the adapters module.

These tests verify that the adapters correctly convert between public and internal data formats.
"""
import pytest

from fogis_api_client.internal.adapters import convert_match_result_to_internal, convert_internal_to_match_result


def test_convert_match_result_to_internal_flat_format():
    """Test converting a flat match result to the internal format."""
    # Flat format (what users work with)
    flat_result = {
        "matchid": 123456,
        "hemmamal": 2,
        "bortamal": 1,
        "halvtidHemmamal": 1,
        "halvtidBortamal": 0
    }
    
    # Convert to internal format
    internal_result = convert_match_result_to_internal(flat_result)
    
    # Verify the structure
    assert "matchresultatListaJSON" in internal_result
    assert len(internal_result["matchresultatListaJSON"]) == 2
    
    # Verify full-time result
    fulltime = internal_result["matchresultatListaJSON"][0]
    assert fulltime["matchid"] == 123456
    assert fulltime["matchresultattypid"] == 1  # Full-time
    assert fulltime["matchlag1mal"] == 2
    assert fulltime["matchlag2mal"] == 1
    assert fulltime["wo"] is False
    assert fulltime["ow"] is False
    assert fulltime["ww"] is False
    
    # Verify half-time result
    halftime = internal_result["matchresultatListaJSON"][1]
    assert halftime["matchid"] == 123456
    assert halftime["matchresultattypid"] == 2  # Half-time
    assert halftime["matchlag1mal"] == 1
    assert halftime["matchlag2mal"] == 0
    assert halftime["wo"] is False
    assert halftime["ow"] is False
    assert halftime["ww"] is False


def test_convert_internal_to_match_result_nested_format():
    """Test converting an internal match result to the public format."""
    # Internal format (what the server expects)
    internal_result = {
        "matchresultatListaJSON": [
            {
                "matchid": 123456,
                "matchresultattypid": 1,  # Full-time
                "matchlag1mal": 2,
                "matchlag2mal": 1,
                "wo": False,
                "ow": False,
                "ww": False
            },
            {
                "matchid": 123456,
                "matchresultattypid": 2,  # Half-time
                "matchlag1mal": 1,
                "matchlag2mal": 0,
                "wo": False,
                "ow": False,
                "ww": False
            }
        ]
    }
    
    # Convert to public format
    public_result = convert_internal_to_match_result(internal_result)
    
    # Verify the structure
    assert "matchid" in public_result
    assert "hemmamal" in public_result
    assert "bortamal" in public_result
    assert "halvtidHemmamal" in public_result
    assert "halvtidBortamal" in public_result
    
    # Verify values
    assert public_result["matchid"] == 123456
    assert public_result["hemmamal"] == 2
    assert public_result["bortamal"] == 1
    assert public_result["halvtidHemmamal"] == 1
    assert public_result["halvtidBortamal"] == 0
