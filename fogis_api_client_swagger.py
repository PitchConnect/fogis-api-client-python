"""
OpenAPI/Swagger documentation for the FOGIS API Gateway.
"""

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_swagger_ui import get_swaggerui_blueprint
from marshmallow import Schema, fields

# Create an APISpec
spec = APISpec(
    title="FOGIS API Gateway",
    version="1.0.0",
    openapi_version="3.0.2",
    info=dict(
        description="HTTP API Gateway for the FOGIS API Client",
        contact=dict(
            name="FOGIS API Gateway",
            url="https://github.com/timmybird/fogis_api_client_python",
        ),
    ),
    plugins=[MarshmallowPlugin()],
)


# Define schemas for request/response models
class ErrorSchema(Schema):
    """Schema for error responses."""

    error = fields.String(required=True, metadata={"description": "Human-readable error message"})
    message = fields.String(required=True, metadata={"description": "Detailed error information"})
    error_type = fields.String(required=True, metadata={"description": "Error type code"})


class MatchSchema(Schema):
    """Schema for match data."""

    id = fields.String(required=True, metadata={"description": "Match ID"})
    home_team = fields.String(required=True, metadata={"description": "Home team name"})
    away_team = fields.String(required=True, metadata={"description": "Away team name"})
    datum = fields.String(metadata={"description": "Match date"})
    tavling = fields.String(metadata={"description": "Competition name"})
    status = fields.String(metadata={"description": "Match status"})


class MatchResultSchema(Schema):
    """Schema for match result data."""

    id = fields.String(required=True, metadata={"description": "Match ID"})
    home_score = fields.Integer(metadata={"description": "Home team score"})
    away_score = fields.Integer(metadata={"description": "Away team score"})


class EventSchema(Schema):
    """Schema for match event data."""

    id = fields.String(metadata={"description": "Event ID"})
    type = fields.String(metadata={"description": "Event type (e.g., goal, card, substitution)"})
    player = fields.String(metadata={"description": "Player name"})
    team = fields.String(metadata={"description": "Team name"})
    time = fields.String(metadata={"description": "Event time"})


class LoginRequestSchema(Schema):
    """Schema for login request."""

    username = fields.String(required=True, metadata={"description": "FOGIS username"})
    password = fields.String(required=True, metadata={"description": "FOGIS password"})


class TokenSchema(Schema):
    """Schema for authentication token (cookies)."""

    token = fields.Dict(keys=fields.String(), values=fields.String(), metadata={"description": "Session cookies"})


class TokenResponseSchema(Schema):
    """Schema for token response."""

    success = fields.Boolean(required=True, metadata={"description": "Whether the operation was successful"})
    message = fields.String(metadata={"description": "Human-readable message"})
    token = fields.Dict(keys=fields.String(), values=fields.String(), metadata={"description": "Session cookies"})
    error = fields.String(metadata={"description": "Error message if operation failed"})


class TokenValidationResponseSchema(Schema):
    """Schema for token validation response."""

    success = fields.Boolean(required=True, metadata={"description": "Whether the operation was successful"})
    valid = fields.Boolean(metadata={"description": "Whether the token is valid"})
    message = fields.String(metadata={"description": "Human-readable message"})
    error = fields.String(metadata={"description": "Error message if operation failed"})


class PlayerSchema(Schema):
    """Schema for player data."""

    id = fields.String(metadata={"description": "Player ID"})
    name = fields.String(metadata={"description": "Player name"})
    position = fields.String(metadata={"description": "Player position"})
    number = fields.String(metadata={"description": "Player jersey number"})


class OfficialSchema(Schema):
    """Schema for official data."""

    id = fields.String(metadata={"description": "Official ID"})
    name = fields.String(metadata={"description": "Official name"})
    role = fields.String(metadata={"description": "Official role"})


# Register schemas with spec
spec.components.schema("Error", schema=ErrorSchema)
spec.components.schema("Match", schema=MatchSchema)
spec.components.schema("MatchResult", schema=MatchResultSchema)
spec.components.schema("Event", schema=EventSchema)
spec.components.schema("Player", schema=PlayerSchema)
spec.components.schema("Official", schema=OfficialSchema)

# Define paths/endpoints
# Root endpoint
spec.path(
    path="/",
    operations={
        "get": {
            "summary": "API status check",
            "description": "Returns a test JSON response to verify the API is working",
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                    "message": {"type": "string"},
                                },
                            }
                        }
                    },
                }
            },
        }
    },
)

# Hello endpoint
spec.path(
    path="/hello",
    operations={
        "get": {
            "summary": "Hello world test",
            "description": "Returns a simple hello world message",
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "string",
                            }
                        }
                    },
                }
            },
        }
    },
)

# Matches endpoint
spec.path(
    path="/matches",
    operations={
        "get": {
            "summary": "Get matches list",
            "description": "Returns a list of matches from FOGIS",
            "parameters": [
                {
                    "name": "from_date",
                    "in": "query",
                    "description": "Start date for filtering matches (format: YYYY-MM-DD)",
                    "schema": {"type": "string", "format": "date"},
                },
                {
                    "name": "to_date",
                    "in": "query",
                    "description": "End date for filtering matches (format: YYYY-MM-DD)",
                    "schema": {"type": "string", "format": "date"},
                },
                {
                    "name": "limit",
                    "in": "query",
                    "description": "Maximum number of matches to return",
                    "schema": {"type": "integer", "minimum": 1},
                },
                {
                    "name": "offset",
                    "in": "query",
                    "description": "Number of matches to skip (for pagination)",
                    "schema": {"type": "integer", "minimum": 0, "default": 0},
                },
                {
                    "name": "sort_by",
                    "in": "query",
                    "description": "Field to sort by",
                    "schema": {
                        "type": "string",
                        "enum": ["datum", "hemmalag", "bortalag", "tavling"],
                        "default": "datum",
                    },
                },
                {
                    "name": "order",
                    "in": "query",
                    "description": "Sort order",
                    "schema": {"type": "string", "enum": ["asc", "desc"], "default": "asc"},
                },
            ],
            "responses": {
                "200": {
                    "description": "List of matches",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Match"},
                            }
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Filtered matches endpoint
spec.path(
    path="/matches/filter",
    operations={
        "post": {
            "summary": "Get filtered matches list",
            "description": "Returns a filtered list of matches based on provided criteria",
            "requestBody": {
                "description": "Filter parameters",
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "from_date": {
                                    "type": "string",
                                    "format": "date",
                                    "description": "Start date for filtering matches",
                                },
                                "to_date": {
                                    "type": "string",
                                    "format": "date",
                                    "description": "End date for filtering matches",
                                },
                                "status": {
                                    "type": "string",
                                    "description": "Match status (e.g., 'upcoming', 'completed')",
                                },
                                "age_category": {
                                    "type": "string",
                                    "description": "Age category for filtering matches",
                                },
                                "gender": {
                                    "type": "string",
                                    "description": "Gender for filtering matches",
                                },
                                "football_type": {
                                    "type": "string",
                                    "description": "Type of football (e.g., 'indoor', 'outdoor')",
                                },
                            },
                        }
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "List of filtered matches",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Match"},
                            }
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Match details endpoint
spec.path(
    path="/match/{match_id}",
    operations={
        "get": {
            "summary": "Get match details",
            "description": "Returns details for a specific match",
            "parameters": [
                {
                    "name": "match_id",
                    "in": "path",
                    "required": True,
                    "description": "Match ID",
                    "schema": {"type": "string"},
                },
                {
                    "name": "include_events",
                    "in": "query",
                    "description": "Whether to include events in the response",
                    "schema": {"type": "boolean", "default": True},
                },
                {
                    "name": "include_players",
                    "in": "query",
                    "description": "Whether to include players in the response",
                    "schema": {"type": "boolean", "default": False},
                },
                {
                    "name": "include_officials",
                    "in": "query",
                    "description": "Whether to include officials in the response",
                    "schema": {"type": "boolean", "default": False},
                },
            ],
            "responses": {
                "200": {
                    "description": "Match details",
                    "content": {
                        "application/json": {
                            "schema": {
                                "allOf": [
                                    {"$ref": "#/components/schemas/Match"},
                                    {
                                        "type": "object",
                                        "properties": {
                                            "events": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Event"},
                                            },
                                            "players": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Player"},
                                            },
                                            "officials": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Official"},
                                            },
                                        },
                                    },
                                ]
                            }
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Match result endpoint
spec.path(
    path="/match/{match_id}/result",
    operations={
        "get": {
            "summary": "Get match result",
            "description": "Returns result information for a specific match",
            "parameters": [
                {
                    "name": "match_id",
                    "in": "path",
                    "required": True,
                    "description": "Match ID",
                    "schema": {"type": "string"},
                },
            ],
            "responses": {
                "200": {
                    "description": "Match result",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/MatchResult"},
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Match events endpoint
spec.path(
    path="/match/{match_id}/events",
    operations={
        "get": {
            "summary": "Get match events",
            "description": "Returns events for a specific match",
            "parameters": [
                {
                    "name": "match_id",
                    "in": "path",
                    "required": True,
                    "description": "Match ID",
                    "schema": {"type": "string"},
                },
                {
                    "name": "type",
                    "in": "query",
                    "description": "Filter events by type",
                    "schema": {"type": "string"},
                },
                {
                    "name": "player",
                    "in": "query",
                    "description": "Filter events by player name",
                    "schema": {"type": "string"},
                },
                {
                    "name": "team",
                    "in": "query",
                    "description": "Filter events by team name",
                    "schema": {"type": "string"},
                },
                {
                    "name": "limit",
                    "in": "query",
                    "description": "Maximum number of events to return",
                    "schema": {"type": "integer", "minimum": 1},
                },
                {
                    "name": "offset",
                    "in": "query",
                    "description": "Number of events to skip (for pagination)",
                    "schema": {"type": "integer", "minimum": 0, "default": 0},
                },
                {
                    "name": "sort_by",
                    "in": "query",
                    "description": "Field to sort by",
                    "schema": {
                        "type": "string",
                        "enum": ["time", "type", "player", "team"],
                        "default": "time",
                    },
                },
                {
                    "name": "order",
                    "in": "query",
                    "description": "Sort order",
                    "schema": {"type": "string", "enum": ["asc", "desc"], "default": "asc"},
                },
            ],
            "responses": {
                "200": {
                    "description": "List of match events",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Event"},
                            }
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        },
        "post": {
            "summary": "Report match event",
            "description": "Reports a new event for a match",
            "parameters": [
                {
                    "name": "match_id",
                    "in": "path",
                    "required": True,
                    "description": "Match ID",
                    "schema": {"type": "string"},
                },
            ],
            "requestBody": {
                "description": "Event data",
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["type"],
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "description": "Event type (e.g., 'goal', 'card')",
                                },
                                "player": {"type": "string", "description": "Player name"},
                                "team": {"type": "string", "description": "Team name"},
                                "time": {"type": "string", "description": "Event time"},
                            },
                        }
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Event reported successfully",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        },
    },
)

# Clear match events endpoint
spec.path(
    path="/match/{match_id}/events/clear",
    operations={
        "post": {
            "summary": "Clear match events",
            "description": "Clears all events for a match",
            "parameters": [
                {
                    "name": "match_id",
                    "in": "path",
                    "required": True,
                    "description": "Match ID",
                    "schema": {"type": "string"},
                },
            ],
            "responses": {
                "200": {
                    "description": "Events cleared successfully",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                },
                            }
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Match officials endpoint
spec.path(
    path="/match/{match_id}/officials",
    operations={
        "get": {
            "summary": "Get match officials",
            "description": "Returns officials information for a specific match",
            "parameters": [
                {
                    "name": "match_id",
                    "in": "path",
                    "required": True,
                    "description": "Match ID",
                    "schema": {"type": "string"},
                },
            ],
            "responses": {
                "200": {
                    "description": "List of match officials",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Official"},
                            }
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Finish match report endpoint
spec.path(
    path="/match/{match_id}/finish",
    operations={
        "post": {
            "summary": "Finish match report",
            "description": "Marks a match report as completed/finished",
            "parameters": [
                {
                    "name": "match_id",
                    "in": "path",
                    "required": True,
                    "description": "Match ID",
                    "schema": {"type": "string"},
                },
            ],
            "responses": {
                "200": {
                    "description": "Match report finished successfully",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "success": {"type": "boolean"},
                                },
                            }
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Team players endpoint
spec.path(
    path="/team/{team_id}/players",
    operations={
        "get": {
            "summary": "Get team players",
            "description": "Returns player information for a specific team",
            "parameters": [
                {
                    "name": "team_id",
                    "in": "path",
                    "required": True,
                    "description": "Team ID",
                    "schema": {"type": "string"},
                },
                {
                    "name": "name",
                    "in": "query",
                    "description": "Filter players by name",
                    "schema": {"type": "string"},
                },
                {
                    "name": "position",
                    "in": "query",
                    "description": "Filter players by position",
                    "schema": {"type": "string"},
                },
                {
                    "name": "number",
                    "in": "query",
                    "description": "Filter players by jersey number",
                    "schema": {"type": "string"},
                },
                {
                    "name": "limit",
                    "in": "query",
                    "description": "Maximum number of players to return",
                    "schema": {"type": "integer", "minimum": 1},
                },
                {
                    "name": "offset",
                    "in": "query",
                    "description": "Number of players to skip (for pagination)",
                    "schema": {"type": "integer", "minimum": 0, "default": 0},
                },
                {
                    "name": "sort_by",
                    "in": "query",
                    "description": "Field to sort by",
                    "schema": {
                        "type": "string",
                        "enum": ["name", "position", "number"],
                        "default": "name",
                    },
                },
                {
                    "name": "order",
                    "in": "query",
                    "description": "Sort order",
                    "schema": {"type": "string", "enum": ["asc", "desc"], "default": "asc"},
                },
            ],
            "responses": {
                "200": {
                    "description": "List of team players",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Player"},
                            }
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Team officials endpoint
spec.path(
    path="/team/{team_id}/officials",
    operations={
        "get": {
            "summary": "Get team officials",
            "description": "Returns officials information for a specific team",
            "parameters": [
                {
                    "name": "team_id",
                    "in": "path",
                    "required": True,
                    "description": "Team ID",
                    "schema": {"type": "string"},
                },
                {
                    "name": "name",
                    "in": "query",
                    "description": "Filter officials by name",
                    "schema": {"type": "string"},
                },
                {
                    "name": "role",
                    "in": "query",
                    "description": "Filter officials by role",
                    "schema": {"type": "string"},
                },
                {
                    "name": "limit",
                    "in": "query",
                    "description": "Maximum number of officials to return",
                    "schema": {"type": "integer", "minimum": 1},
                },
                {
                    "name": "offset",
                    "in": "query",
                    "description": "Number of officials to skip (for pagination)",
                    "schema": {"type": "integer", "minimum": 0, "default": 0},
                },
                {
                    "name": "sort_by",
                    "in": "query",
                    "description": "Field to sort by",
                    "schema": {"type": "string", "enum": ["name", "role"], "default": "name"},
                },
                {
                    "name": "order",
                    "in": "query",
                    "description": "Sort order",
                    "schema": {"type": "string", "enum": ["asc", "desc"], "default": "asc"},
                },
            ],
            "responses": {
                "200": {
                    "description": "List of team officials",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Official"},
                            }
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Authentication endpoints

# Login endpoint
spec.path(
    path="/auth/login",
    operations={
        "post": {
            "summary": "Login to FOGIS API",
            "description": "Authenticates with FOGIS API and returns a token (cookies)",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/LoginRequestSchema"},
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Login successful",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TokenResponseSchema"},
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "401": {
                    "description": "Authentication failed",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Validate endpoint
spec.path(
    path="/auth/validate",
    operations={
        "post": {
            "summary": "Validate token",
            "description": "Checks if a token (cookies) is still valid",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TokenSchema"},
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Validation result",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TokenValidationResponseSchema"},
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Refresh endpoint
spec.path(
    path="/auth/refresh",
    operations={
        "post": {
            "summary": "Refresh token",
            "description": "Refreshes a token (cookies) if it's still valid",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TokenSchema"},
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Refresh successful",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TokenResponseSchema"},
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "401": {
                    "description": "Token is invalid or expired",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)

# Logout endpoint
spec.path(
    path="/auth/logout",
    operations={
        "post": {
            "summary": "Logout from FOGIS API",
            "description": "Invalidates a token (cookies)",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TokenSchema"},
                    }
                },
            },
            "responses": {
                "200": {
                    "description": "Logout successful",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/TokenResponseSchema"},
                        }
                    },
                },
                "400": {
                    "description": "Invalid input",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
                "500": {
                    "description": "Server error",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Error"},
                        }
                    },
                },
            },
        }
    },
)


# Function to get the Swagger UI blueprint
def get_swagger_blueprint():
    """
    Returns the Swagger UI blueprint for the FOGIS API Gateway.
    """
    SWAGGER_URL = "/api/docs"  # URL for exposing Swagger UI
    API_URL = "/api/swagger.json"  # URL for the API spec

    # Create Swagger UI blueprint
    swagger_ui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            "app_name": "FOGIS API Client",
            "validatorUrl": None,  # Disable validator
        },
    )

    return swagger_ui_blueprint, SWAGGER_URL, API_URL
