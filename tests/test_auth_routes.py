import json
import unittest
from unittest.mock import patch

from flask import Flask

from auth_routes import register_auth_routes
from fogis_api_client.public_api_client import FogisLoginError


class TestAuthRoutes(unittest.TestCase):
    """Test cases for the authentication routes."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test Flask app
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True

        # Register the authentication routes
        register_auth_routes(self.app)

        # Create a test client
        self.client = self.app.test_client()

        # Sample test data
        self.test_username = "test_user"
        self.test_password = "test_pass"
        self.test_cookies = {
            "FogisMobilDomarKlient.ASPXAUTH": "test_auth_cookie",
            "ASP.NET_SessionId": "test_session_id",
        }

    @patch("auth_routes.PublicApiClient")
    def test_login_success(self, mock_fogis_client):
        """Test successful login."""
        # Configure the mock
        mock_instance = mock_fogis_client.return_value
        mock_instance.login.return_value = self.test_cookies

        # Make the request
        response = self.client.post(
            "/auth/login",
            data=json.dumps({"username": self.test_username, "password": self.test_password}),
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["token"], self.test_cookies)

        # Verify the mock was called correctly
        mock_fogis_client.assert_called_once_with(username=self.test_username, password=self.test_password)
        mock_instance.login.assert_called_once()

    @patch("auth_routes.PublicApiClient")
    def test_login_failure(self, mock_fogis_client):
        """Test login failure."""
        # Configure the mock to raise an exception
        mock_instance = mock_fogis_client.return_value
        mock_instance.login.side_effect = FogisLoginError("Invalid credentials")

        # Make the request
        response = self.client.post(
            "/auth/login",
            data=json.dumps({"username": self.test_username, "password": self.test_password}),
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("error", data)

        # Verify the mock was called correctly
        mock_fogis_client.assert_called_once_with(username=self.test_username, password=self.test_password)
        mock_instance.login.assert_called_once()

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        # Test with missing username
        response = self.client.post(
            "/auth/login",
            data=json.dumps({"password": self.test_password}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

        # Test with missing password
        response = self.client.post(
            "/auth/login",
            data=json.dumps({"username": self.test_username}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

        # Test with empty request
        response = self.client.post("/auth/login", data=json.dumps({}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_login_wrong_content_type(self):
        """Test login with wrong content type."""
        response = self.client.post(
            "/auth/login",
            data=f"username={self.test_username}&password={self.test_password}",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 415)

    @patch("auth_routes.PublicApiClient")
    def test_validate_valid_token(self, mock_fogis_client):
        """Test token validation with valid token."""
        # Configure the mock
        mock_instance = mock_fogis_client.return_value
        mock_instance.validate_cookies.return_value = True

        # Make the request
        response = self.client.post(
            "/auth/validate",
            data=json.dumps({"token": self.test_cookies}),
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertTrue(data["valid"])

        # Verify the mock was called correctly
        mock_fogis_client.assert_called_once_with(cookies=self.test_cookies)
        mock_instance.validate_cookies.assert_called_once()

    @patch("auth_routes.PublicApiClient")
    def test_validate_invalid_token(self, mock_fogis_client):
        """Test token validation with invalid token."""
        # Configure the mock
        mock_instance = mock_fogis_client.return_value
        mock_instance.validate_cookies.return_value = False

        # Make the request
        response = self.client.post(
            "/auth/validate",
            data=json.dumps({"token": self.test_cookies}),
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertFalse(data["valid"])

        # Verify the mock was called correctly
        mock_fogis_client.assert_called_once_with(cookies=self.test_cookies)
        mock_instance.validate_cookies.assert_called_once()

    def test_validate_missing_token(self):
        """Test token validation with missing token."""
        response = self.client.post("/auth/validate", data=json.dumps({}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    @patch("auth_routes.PublicApiClient")
    def test_refresh_valid_token(self, mock_fogis_client):
        """Test token refresh with valid token."""
        # Configure the mock
        mock_instance = mock_fogis_client.return_value
        mock_instance.validate_cookies.return_value = True

        # Make the request
        response = self.client.post(
            "/auth/refresh",
            data=json.dumps({"token": self.test_cookies}),
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["token"], self.test_cookies)

        # Verify the mock was called correctly
        mock_fogis_client.assert_called_once_with(cookies=self.test_cookies)
        mock_instance.validate_cookies.assert_called_once()

    @patch("auth_routes.PublicApiClient")
    def test_refresh_invalid_token(self, mock_fogis_client):
        """Test token refresh with invalid token."""
        # Configure the mock
        mock_instance = mock_fogis_client.return_value
        mock_instance.validate_cookies.return_value = False

        # Make the request
        response = self.client.post(
            "/auth/refresh",
            data=json.dumps({"token": self.test_cookies}),
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertFalse(data["valid"])

        # Verify the mock was called correctly
        mock_fogis_client.assert_called_once_with(cookies=self.test_cookies)
        mock_instance.validate_cookies.assert_called_once()

    def test_refresh_missing_token(self):
        """Test token refresh with missing token."""
        response = self.client.post("/auth/refresh", data=json.dumps({}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_logout_success(self):
        """Test successful logout."""
        # Make the request
        response = self.client.post(
            "/auth/logout",
            data=json.dumps({"token": self.test_cookies}),
            content_type="application/json",
        )

        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("message", data)

    def test_logout_missing_token(self):
        """Test logout with missing token."""
        response = self.client.post("/auth/logout", data=json.dumps({}), content_type="application/json")
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
