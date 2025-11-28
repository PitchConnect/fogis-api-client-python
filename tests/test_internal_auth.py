"""
Tests for internal authentication module.

This module tests the authentication functionality to improve
code coverage for the internal auth components.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from fogis_api_client.internal.auth import FogisAuthenticationError, authenticate


class TestInternalAuth:
    """Test suite for internal authentication functionality."""

    def test_authenticate_success(self):
        """Test successful authentication with proper form fields."""
        # Mock session
        mock_session = Mock(spec=requests.Session)
        mock_session.headers = {}

        # Mock login page response with proper hidden inputs
        login_response = Mock()
        login_response.url = "http://example.com/Login.aspx"  # ASP.NET URL, not OAuth
        login_response.text = """
        <html>
            <form>
                <input type="hidden" name="__VIEWSTATE" value="test_viewstate" />
                <input type="hidden" name="__VIEWSTATEGENERATOR" value="test_generator" />
                <input type="hidden" name="__EVENTVALIDATION" value="test_validation" />
            </form>
        </html>
        """
        login_response.raise_for_status = Mock()

        # Mock authentication response
        auth_response = Mock()
        auth_response.url = "http://example.com/mdk/"
        auth_response.raise_for_status = Mock()

        # Mock session.get and session.post
        mock_session.get.return_value = login_response
        mock_session.post.return_value = auth_response

        # Mock cookies with the expected authentication cookie
        mock_session.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "test_auth_token"}

        result = authenticate(mock_session, "testuser", "testpass", "http://example.com")

        # Verify the result contains the auth token
        assert "FogisMobilDomarKlient.ASPXAUTH" in result
        assert result["FogisMobilDomarKlient.ASPXAUTH"] == "test_auth_token"

        # Verify session headers were set
        assert "User-Agent" in mock_session.headers
        assert "Mozilla" in mock_session.headers["User-Agent"]

        # Verify login page was requested
        mock_session.get.assert_called_once()

        # Verify authentication was attempted
        mock_session.post.assert_called_once()

    def test_authenticate_login_page_request_failure(self):
        """Test authentication when login page request fails."""
        mock_session = Mock(spec=requests.Session)
        mock_session.headers = {}
        mock_session.get.side_effect = requests.exceptions.RequestException("Connection failed")

        with pytest.raises(FogisAuthenticationError, match="Network error during authentication"):
            authenticate(mock_session, "testuser", "testpass", "http://example.com")

    def test_authenticate_missing_viewstate(self):
        """Test authentication when login page is missing __VIEWSTATE."""
        mock_session = Mock(spec=requests.Session)
        mock_session.headers = {}

        # Mock login page response without __VIEWSTATE
        login_response = Mock()
        login_response.url = "http://example.com/Login.aspx"  # ASP.NET URL, not OAuth
        login_response.text = "<html><form></form></html>"
        login_response.raise_for_status = Mock()

        mock_session.get.return_value = login_response

        with pytest.raises(FogisAuthenticationError, match="Failed to extract __VIEWSTATE token"):
            authenticate(mock_session, "testuser", "testpass", "http://example.com")

    def test_authenticate_missing_eventvalidation(self):
        """Test authentication when login page is missing __EVENTVALIDATION."""
        mock_session = Mock(spec=requests.Session)
        mock_session.headers = {}

        # Mock login page response with __VIEWSTATE but no __EVENTVALIDATION
        login_response = Mock()
        login_response.url = "http://example.com/Login.aspx"  # ASP.NET URL, not OAuth
        login_response.text = """
        <html>
            <form>
                <input type="hidden" name="__VIEWSTATE" value="test_viewstate" />
            </form>
        </html>
        """
        login_response.raise_for_status = Mock()

        mock_session.get.return_value = login_response

        with pytest.raises(FogisAuthenticationError, match="Failed to extract __EVENTVALIDATION token"):
            authenticate(mock_session, "testuser", "testpass", "http://example.com")

    def test_authenticate_invalid_credentials(self):
        """Test authentication with invalid credentials (no auth cookie)."""
        mock_session = Mock(spec=requests.Session)
        mock_session.headers = {}

        # Mock login page response
        login_response = Mock()
        login_response.url = "http://example.com/Login.aspx"  # ASP.NET URL, not OAuth
        login_response.text = """
        <html>
            <form>
                <input type="hidden" name="__VIEWSTATE" value="test_viewstate" />
                <input type="hidden" name="__VIEWSTATEGENERATOR" value="test_generator" />
                <input type="hidden" name="__EVENTVALIDATION" value="test_validation" />
            </form>
        </html>
        """
        login_response.raise_for_status = Mock()

        # Mock authentication response without the auth cookie
        auth_response = Mock()
        auth_response.url = "http://example.com/Login.aspx?error=invalid"
        auth_response.raise_for_status = Mock()

        mock_session.get.return_value = login_response
        mock_session.post.return_value = auth_response
        mock_session.cookies = {}  # No auth cookie

        with pytest.raises(FogisAuthenticationError, match="ASP.NET authentication failed"):
            authenticate(mock_session, "testuser", "wrongpass", "http://example.com")

    def test_authenticate_headers_configuration(self):
        """Test that browser-like headers are correctly configured."""
        mock_session = Mock(spec=requests.Session)
        mock_session.headers = {}

        # Mock minimal successful flow
        login_response = Mock()
        login_response.url = "http://example.com/Login.aspx"  # ASP.NET URL, not OAuth
        login_response.text = """
        <html>
            <form>
                <input type="hidden" name="__VIEWSTATE" value="test" />
                <input type="hidden" name="__VIEWSTATEGENERATOR" value="test" />
                <input type="hidden" name="__EVENTVALIDATION" value="test" />
            </form>
        </html>
        """
        login_response.raise_for_status = Mock()

        auth_response = Mock()
        auth_response.url = "http://example.com/mdk/"
        auth_response.raise_for_status = Mock()

        mock_session.get.return_value = login_response
        mock_session.post.return_value = auth_response
        mock_session.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "test_token"}

        authenticate(mock_session, "testuser", "testpass", "http://example.com")

        # Verify headers were set
        headers = mock_session.headers
        assert "User-Agent" in headers
        assert "Chrome" in headers["User-Agent"]
        assert headers["Accept-Language"] == "sv-SE,sv;q=0.9,en;q=0.8"
        assert headers["Connection"] == "keep-alive"

    def test_authenticate_post_request_failure(self):
        """Test authentication when POST request fails."""
        mock_session = Mock(spec=requests.Session)
        mock_session.headers = {}

        # Mock successful login page response
        login_response = Mock()
        login_response.url = "http://example.com/Login.aspx"  # ASP.NET URL, not OAuth
        login_response.text = """
        <html>
            <form>
                <input type="hidden" name="__VIEWSTATE" value="test_viewstate" />
                <input type="hidden" name="__VIEWSTATEGENERATOR" value="test_generator" />
                <input type="hidden" name="__EVENTVALIDATION" value="test_validation" />
            </form>
        </html>
        """
        login_response.raise_for_status = Mock()

        mock_session.get.return_value = login_response
        mock_session.post.side_effect = requests.exceptions.RequestException("Auth failed")

        with pytest.raises(FogisAuthenticationError, match="Network error during authentication"):
            authenticate(mock_session, "testuser", "testpass", "http://example.com")


class TestOAuthAuthenticationPaths:
    """Test OAuth authentication paths in auth module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.session = requests.Session()
        self.username = "test_user"
        self.password = "test_password"

    @patch("fogis_api_client.internal.auth._handle_oauth_login_form")
    def test_handle_oauth_authentication_authorize_endpoint(self, mock_login_form):
        """Test OAuth authentication at authorize endpoint."""
        from fogis_api_client.internal.auth import _handle_oauth_authentication

        oauth_url = "https://auth.fogis.se/connect/authorize?client_id=test"
        mock_login_form.return_value = {"oauth_authenticated": True}

        result = _handle_oauth_authentication(self.session, self.username, self.password, oauth_url)

        assert result == {"oauth_authenticated": True}
        mock_login_form.assert_called_once()

    @patch("fogis_api_client.internal.auth._handle_oauth_login_form")
    def test_handle_oauth_authentication_login_endpoint(self, mock_login_form):
        """Test OAuth authentication at login endpoint."""
        from fogis_api_client.internal.auth import _handle_oauth_authentication

        oauth_url = "https://auth.fogis.se/Account/LogIn?returnUrl=test"
        mock_login_form.return_value = {"oauth_authenticated": True}

        result = _handle_oauth_authentication(self.session, self.username, self.password, oauth_url)

        assert result == {"oauth_authenticated": True}
        mock_login_form.assert_called_once()

    def test_handle_oauth_authentication_unexpected_url(self):
        """Test OAuth authentication with unexpected URL."""
        from fogis_api_client.internal.auth import FogisOAuthAuthenticationError, _handle_oauth_authentication

        oauth_url = "https://example.com/unexpected"

        with pytest.raises(FogisOAuthAuthenticationError):
            _handle_oauth_authentication(self.session, oauth_url, self.username, self.password)

    def test_handle_oauth_authentication_exception(self):
        """Test OAuth authentication with general exception."""
        from fogis_api_client.internal.auth import FogisOAuthAuthenticationError, _handle_oauth_authentication

        # Pass invalid session to trigger exception
        with pytest.raises(FogisOAuthAuthenticationError):
            _handle_oauth_authentication(None, "https://auth.fogis.se/connect/authorize", self.username, self.password)

    @patch("requests.Session.get")
    def test_get_oauth_login_page_success(self, mock_get):
        """Test getting OAuth login page successfully."""
        from fogis_api_client.internal.auth import _get_oauth_login_page
        from fogis_api_client.internal.fogis_oauth_manager import FogisOAuthManager

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>Login form</html>"
        mock_get.return_value = mock_response

        oauth_manager = FogisOAuthManager(self.session)

        result = _get_oauth_login_page(self.session, oauth_manager)
        assert result == mock_response

    @patch("requests.Session.get")
    def test_get_oauth_login_page_failure(self, mock_get):
        """Test getting OAuth login page with failure."""
        from fogis_api_client.internal.auth import _get_oauth_login_page
        from fogis_api_client.internal.fogis_oauth_manager import FogisOAuthManager

        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        oauth_manager = FogisOAuthManager(self.session)

        with pytest.raises(requests.exceptions.RequestException):
            _get_oauth_login_page(self.session, oauth_manager)
