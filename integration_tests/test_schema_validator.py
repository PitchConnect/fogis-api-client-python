"""
Tests for the schema validator.
"""

import json
import os
import pytest
from jsonschema.exceptions import ValidationError

from integration_tests.schema_validator import SchemaValidator


class TestSchemaValidator:
    """Tests for the SchemaValidator class."""

    def test_load_schema(self):
        """Test loading a schema."""
        schema = SchemaValidator.load_schema("match_schema.json")
        assert schema is not None
        assert schema["title"] == "Match Schema"
        assert schema["type"] == "object"

    def test_validate_match_valid(self):
        """Test validating valid match data."""
        # Load a sample match from a file
        sample_path = os.path.join(os.path.dirname(__file__), "sample_data", "match.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                match_data = json.load(f)
            assert SchemaValidator.validate_match(match_data)
        else:
            # Create a minimal valid match
            match_data = {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchJSON",
                "value": "000402010",
                "label": "000402010: Team A - Team B (League), 2025-05-06 17:00",
                "matchid": 12345,
                "matchnr": "000402010",
                "fotbollstypid": 1,
                "matchlag1id": 1001,
                "lag1lagid": 2001,
                "lag1namn": "Team A",
                "matchlag2id": 1002,
                "lag2lagid": 2002,
                "lag2namn": "Team B",
                "tid": "/Date(1746543600000)/",
                "speldatum": "2025-05-06",
                "avsparkstid": "17:00",
                "tavlingid": 3001,
                "tavlingnamn": "League"
            }
            assert SchemaValidator.validate_match(match_data)

    def test_validate_match_invalid(self):
        """Test validating invalid match data."""
        # Missing required fields
        match_data = {
            "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchJSON",
            "value": "000402010"
            # Missing other required fields
        }
        with pytest.raises(ValidationError):
            SchemaValidator.validate_match(match_data)

    def test_validate_match_event_valid(self):
        """Test validating valid match event data."""
        # Load a sample event from a file
        sample_path = os.path.join(os.path.dirname(__file__), "sample_data", "match_event.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                event_data = json.load(f)
            assert SchemaValidator.validate_match_event(event_data)
        else:
            # Create a minimal valid event
            event_data = {
                "matchhandelseid": 12345,
                "matchid": 67890,
                "period": 1,
                "matchminut": 23,
                "matchhandelsetypid": 1,
                "matchlagid": 1001,
                "spelareid": 2001,
                "hemmamal": 1,
                "bortamal": 0
            }
            assert SchemaValidator.validate_match_event(event_data)

    def test_validate_match_event_invalid(self):
        """Test validating invalid match event data."""
        # Missing required fields
        event_data = {
            "matchhandelseid": 12345,
            "matchid": 67890
            # Missing other required fields
        }
        with pytest.raises(ValidationError):
            SchemaValidator.validate_match_event(event_data)

    def test_validate_match_result_valid(self):
        """Test validating valid match result data."""
        # Load a sample result from a file
        sample_path = os.path.join(os.path.dirname(__file__), "sample_data", "match_results.json")
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                results_data = json.load(f)
            # Validate the first result
            assert SchemaValidator.validate_match_result(results_data[0])
            # Validate the second result
            assert SchemaValidator.validate_match_result(results_data[1])
        else:
            # Create a minimal valid result based on real data
            result_data = {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchresultatJSON",
                "matchresultatid": 4694381,
                "matchid": 6169946,
                "matchresultattypid": 1,
                "matchresultattypnamn": "Slutresultat",
                "matchlag1mal": 3,
                "matchlag2mal": 1,
                "wo": False,
                "ow": False,
                "ww": False
            }
            assert SchemaValidator.validate_match_result(result_data)

    def test_validate_match_officials_valid(self):
        """Test validating valid match officials data."""
        # Create a minimal valid officials data
        officials_data = {
            "hemmalag": [
                {
                    "personid": 12345,
                    "fornamn": "John",
                    "efternamn": "Doe",
                    "roll": "Tränare",
                    "matchlagid": 1001
                }
            ],
            "bortalag": [
                {
                    "personid": 67890,
                    "fornamn": "Jane",
                    "efternamn": "Smith",
                    "roll": "Assisterande tränare",
                    "matchlagid": 1002
                }
            ]
        }
        assert SchemaValidator.validate_match_officials(officials_data)

    def test_validate_match_participants_valid(self):
        """Test validating valid match participants data."""
        # Create a minimal valid participants data
        participants_data = {
            "matchdeltagarlista": [
                {
                    "matchdeltagarid": 12345,
                    "matchid": 67890,
                    "matchlagid": 1001,
                    "spelareid": 2001,
                    "fornamn": "John",
                    "efternamn": "Doe",
                    "startspelare": True
                }
            ]
        }
        assert SchemaValidator.validate_match_participants(participants_data)
