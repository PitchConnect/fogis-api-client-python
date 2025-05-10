"""
Schema validator for FOGIS API responses.

This module provides utilities for validating API responses against JSON schemas.
"""

import json
import os
from typing import Any, Dict, List, Optional, Union

import jsonschema


class SchemaValidator:
    """Validator for FOGIS API responses."""

    SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")

    @classmethod
    def load_schema(cls, schema_name: str) -> Dict[str, Any]:
        """
        Load a schema from the schemas directory.

        Args:
            schema_name: Name of the schema file (e.g., "match_schema.json")

        Returns:
            Dict[str, Any]: The loaded schema
        """
        schema_path = os.path.join(cls.SCHEMA_DIR, schema_name)
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def validate(cls, data: Any, schema_name: str) -> bool:
        """
        Validate data against a schema.

        Args:
            data: The data to validate
            schema_name: Name of the schema file (e.g., "match_schema.json")

        Returns:
            bool: True if the data is valid, False otherwise

        Raises:
            jsonschema.exceptions.ValidationError: If the data is invalid
        """
        schema = cls.load_schema(schema_name)
        jsonschema.validate(instance=data, schema=schema)
        return True

    @classmethod
    def validate_match(cls, match_data: Dict[str, Any]) -> bool:
        """
        Validate match data.

        Args:
            match_data: The match data to validate

        Returns:
            bool: True if the data is valid, False otherwise

        Raises:
            jsonschema.exceptions.ValidationError: If the data is invalid
        """
        return cls.validate(match_data, "match_schema.json")

    @classmethod
    def validate_match_event(cls, event_data: Dict[str, Any]) -> bool:
        """
        Validate match event data.

        Args:
            event_data: The match event data to validate

        Returns:
            bool: True if the data is valid, False otherwise

        Raises:
            jsonschema.exceptions.ValidationError: If the data is invalid
        """
        return cls.validate(event_data, "match_event_schema.json")

    @classmethod
    def validate_match_result(cls, result_data: Dict[str, Any]) -> bool:
        """
        Validate match result data.

        Args:
            result_data: The match result data to validate

        Returns:
            bool: True if the data is valid, False otherwise

        Raises:
            jsonschema.exceptions.ValidationError: If the data is invalid
        """
        return cls.validate(result_data, "match_result_schema.json")

    @classmethod
    def validate_match_officials(cls, officials_data: Dict[str, Any]) -> bool:
        """
        Validate match officials data.

        Args:
            officials_data: The match officials data to validate

        Returns:
            bool: True if the data is valid, False otherwise

        Raises:
            jsonschema.exceptions.ValidationError: If the data is invalid
        """
        return cls.validate(officials_data, "match_officials_schema.json")

    @classmethod
    def validate_match_participant(cls, participant_data: Dict[str, Any]) -> bool:
        """
        Validate a single match participant data.

        Args:
            participant_data: The match participant data to validate

        Returns:
            bool: True if the data is valid, False otherwise

        Raises:
            jsonschema.exceptions.ValidationError: If the data is invalid
        """
        return cls.validate(participant_data, "match_participants_schema.json")

    @classmethod
    def validate_match_participants(cls, participants_data: List[Dict[str, Any]]) -> bool:
        """
        Validate a list of match participants data.

        Args:
            participants_data: The list of match participants data to validate

        Returns:
            bool: True if all data is valid, False otherwise

        Raises:
            jsonschema.exceptions.ValidationError: If any data is invalid
        """
        for participant in participants_data:
            cls.validate_match_participant(participant)
        return True
