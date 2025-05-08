# API Validation Layer

The FOGIS API Client includes a validation layer that ensures the data structures sent to and received from the FOGIS API are correct. This helps prevent issues where changes to the client code might break compatibility with the server API.

## How Validation Works

The validation layer uses JSON Schema to define the expected structure of API requests and responses. When you make an API request, the client automatically validates the request payload before sending it to the server. Similarly, when a response is received, it can be validated against the expected schema.

## Configuration Options

You can configure the validation behavior using the `ValidationConfig` class:

```python
from fogis_api_client import ValidationConfig

# Enable or disable validation
ValidationConfig.enable_validation = True  # Default: True

# Set strict mode (raises exceptions on validation failure)
ValidationConfig.strict_mode = True  # Default: True

# Log successful validations
ValidationConfig.log_validation_success = True  # Default: True
```

### Configuration Options Explained

- **enable_validation**: When set to `True`, all API requests and responses will be validated. When set to `False`, validation is skipped entirely.
- **strict_mode**: When set to `True`, validation failures will raise exceptions. When set to `False`, validation failures will be logged but will not interrupt the API request.
- **log_validation_success**: When set to `True`, successful validations will be logged at the debug level. When set to `False`, only validation failures will be logged.

## Validation Errors

When validation fails in strict mode, the client will raise one of the following exceptions:

- `ValidationError`: Raised when the payload or response does not match the expected schema.
- `ValueError`: Raised when no schema is defined for the endpoint.
- `FogisDataError`: Raised when validation fails during an API request.

## Manual Validation

You can also manually validate payloads and responses using the validation functions:

```python
from fogis_api_client import validate_request, validate_response

# Validate a request payload
try:
    validate_request('/MatchWebMetoder.aspx/SparaMatchresultatLista', payload)
    # Payload is valid
except ValidationError as e:
    # Handle validation error
    print(f"Invalid payload: {e}")

# Validate a response
try:
    validate_response('/MatchWebMetoder.aspx/GetMatchresultatlista', response_data)
    # Response is valid
except ValidationError as e:
    # Handle validation error
    print(f"Invalid response: {e}")
```

## Handling Validation Errors

When validation fails, you have several options:

1. **Fix the payload**: Ensure your payload matches the expected schema.
2. **Disable strict mode**: Set `ValidationConfig.strict_mode = False` to log validation errors without raising exceptions.
3. **Disable validation**: Set `ValidationConfig.enable_validation = False` to skip validation entirely.

## Performance Considerations

Validation adds some overhead to API requests. If performance is a concern, you can:

1. **Disable validation in production**: Set `ValidationConfig.enable_validation = False` in production environments.
2. **Disable logging of successful validations**: Set `ValidationConfig.log_validation_success = False` to reduce log volume.

## Adding New Schemas

If you're extending the client with new API endpoints, you should add schemas for those endpoints in the `api_contracts.py` file:

```python
# Define a new schema
NEW_ENDPOINT_SCHEMA = {
    "type": "object",
    "required": ["required_field"],
    "properties": {
        "required_field": {"type": "string"},
        "optional_field": {"type": "integer"}
    },
    "additionalProperties": False
}

# Add the schema to REQUEST_SCHEMAS
REQUEST_SCHEMAS["/MatchWebMetoder.aspx/NewEndpoint"] = NEW_ENDPOINT_SCHEMA
```

## Troubleshooting

If you encounter validation errors, check the following:

1. **Schema exists**: Ensure a schema is defined for the endpoint you're using.
2. **Payload structure**: Verify your payload matches the expected structure.
3. **Required fields**: Make sure all required fields are present in your payload.
4. **Field types**: Ensure field types match the schema (e.g., integers for IDs, strings for text).
5. **Logs**: Check the logs for detailed validation error messages.
