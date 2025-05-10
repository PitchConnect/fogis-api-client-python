# FOGIS API Schemas

This directory contains JSON Schema definitions for the FOGIS API responses. These schemas serve multiple purposes:

1. **Documentation**: They document the expected structure of API responses
2. **Validation**: They can be used to validate responses from both the real API and the mock server
3. **Mock Data Generation**: They guide the generation of realistic mock data
4. **Client Development**: They help developers understand the API contract

## Available Schemas

- `match_schema.json`: Schema for match data from the FOGIS API
- `match_event_schema.json`: Schema for match event data
- `match_result_schema.json`: Schema for match result data
- `match_officials_schema.json`: Schema for match officials data
- `match_participants_schema.json`: Schema for match participants (players) data

## Using the Schemas

### For Validation

You can use these schemas to validate API responses in your tests:

```python
import jsonschema
import json

# Load the schema
with open("integration_tests/schemas/match_schema.json", "r") as f:
    match_schema = json.load(f)

# Validate a response
jsonschema.validate(instance=response_data, schema=match_schema)
```

### For Mock Data Generation

The `MockDataFactory` class should use these schemas to ensure that generated data matches the expected structure:

```python
def generate_match_data(self, match_id=None):
    """Generate mock match data that conforms to the match schema."""
    # Generate data according to the schema
    # ...
```

### For Documentation

These schemas serve as documentation for the API contract. Developers can refer to them to understand the structure of API responses.

## Schema Format

The schemas follow the [JSON Schema](https://json-schema.org/) specification (Draft 7). Each schema includes:

- Property definitions with types and descriptions
- Example values for each property
- Required properties
- Nested object definitions

## Maintaining Schemas

When the API changes, please update the corresponding schema to reflect the changes. This ensures that our documentation and validation remain accurate.

## Adding New Schemas

To add a new schema:

1. Create a new JSON file in this directory
2. Follow the existing schema format
3. Include all properties with types, descriptions, and examples
4. List required properties
5. Update this README to include the new schema
