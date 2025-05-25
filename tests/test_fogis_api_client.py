import io
import logging
import unittest
from unittest.mock import MagicMock, Mock

import requests

from fogis_api_client.fogis_api_client import FogisApiClient, FogisAPIRequestError, FogisLoginError


class MockResponse:
    """
    A mock class to simulate requests.Response for testing.
    """

    def __init__(self, json_data, status_code):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise requests.exceptions.HTTPError(f"HTTP Error {self.status_code}", response=self)


class TestFogisApiClient(unittest.TestCase):
    """Test cases for the FogisApiClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = FogisApiClient("testuser", "testpassword")

        # Create a mock session
        mock_session = Mock()
        mock_session.get = MagicMock()
        mock_session.post = MagicMock()
        mock_session.cookies = MagicMock(spec=dict)
        mock_session.cookies.set = MagicMock()

        self.client.session = mock_session
        self.client.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}  # Simulate being logged in

        # Set up logging capture
        self.log_capture = io.StringIO()
        self.log_handler = logging.StreamHandler(self.log_capture)
        self.logger = logging.getLogger("fogis_api_client.fogis_api_client")
        self.logger.addHandler(self.log_handler)
        self.logger.setLevel(logging.INFO)

    def tearDown(self):
        """Tear down test fixtures."""
        self.logger.removeHandler(self.log_handler)
        self.log_handler.close()

    def test_login_success(self):
        """Unit test for successful login."""
        # Create a client without cookies
        client = FogisApiClient("testuser", "testpassword")

        # Mock the session
        mocked_session = Mock()
        client.session = mocked_session

        # Mock the get response to return a valid login page
        mock_get_response = Mock()
        mock_get_response.text = (
            '<input name="__VIEWSTATE" value="viewstate_value" />'
            '<input name="__EVENTVALIDATION" value="eventvalidation_value" />'
        )
        mocked_session.get.return_value = mock_get_response

        # Mock the post response for successful login (302 redirect)
        mock_post_response = Mock()
        mock_post_response.status_code = 302
        mock_post_response.headers = {"Location": "/mdk/"}
        mock_post_response.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}
        mocked_session.post.return_value = mock_post_response

        # Mock the redirect response
        mock_redirect_response = Mock()
        mocked_session.get.side_effect = [mock_get_response, mock_redirect_response]

        # Mock the cookies to simulate successful login
        mocked_session.cookies = {"FogisMobilDomarKlient.ASPXAUTH": "mock_auth_cookie"}

        # Call login
        cookies = client.login()

        # Verify the result
        self.assertIn("FogisMobilDomarKlient.ASPXAUTH", cookies)
        self.assertEqual(cookies["FogisMobilDomarKlient.ASPXAUTH"], "mock_auth_cookie")
        self.assertEqual(mocked_session.get.call_count, 2)  # Initial page load + redirect
        mocked_session.post.assert_called_once()

    def test_login_failure_invalid_credentials(self):
        """Unit test for login failure due to invalid credentials."""
        # Create a client without cookies
        client = FogisApiClient("testuser", "testpassword")

        # Mock the session
        mocked_session = Mock()
        client.session = mocked_session

        # Mock the get response to return a valid login page
        mock_get_response = Mock()
        mock_get_response.text = (
            '<input name="__VIEWSTATE" value="viewstate_value" />'
            '<input name="__EVENTVALIDATION" value="eventvalidation_value" />'
        )
        mocked_session.get.return_value = mock_get_response

        # Mock the post response to simulate failed login for both field name attempts
        mock_post_response = Mock()
        mock_post_response.status_code = 200  # Not a redirect
        # Make both post calls return the same failed response
        mocked_session.post.return_value = mock_post_response

        # Make post only return one response to simplify the test
        mocked_session.post = Mock(return_value=mock_post_response)

        # Mock the cookies to simulate failed login (no auth cookie)
        mocked_session.cookies = {}

        # Call login and expect an exception
        with self.assertRaises(FogisLoginError):
            client.login()

        mocked_session.get.assert_called_once()
        # Verify that the post method was called once
        mocked_session.post.assert_called_once()

    def test_api_request_success(self):
        """Unit test for successful _api_request POST."""
        # Mock the session's post method
        mock_session_instance = self.client.session
        url = f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SomeEndpoint"
        payload = {"param1": "value1"}

        # Create a mock response
        mock_api_response = MockResponse({"d": '{"key": "value"}'}, 200)
        mock_session_instance.post.return_value = mock_api_response

        # Call _api_request
        response_data = self.client._api_request(url, payload, method="POST")

        # Verify the result
        self.assertEqual(response_data, {"key": "value"})
        mock_session_instance.post.assert_called_once_with(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Origin": "https://fogis.svenskfotboll.se",
                "Referer": f"{FogisApiClient.BASE_URL}/",
                "X-Requested-With": "XMLHttpRequest",
                "Cookie": "FogisMobilDomarKlient.ASPXAUTH=mock_auth_cookie",
            },
        )

    def test_api_request_get_success(self):
        """Unit test for successful _api_request GET."""
        # Mock the session's get method
        mock_session_instance = self.client.session
        url = f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetSomeData"

        # Create a mock response
        mock_api_response = MockResponse({"d": '{"items": [1, 2, 3]}'}, 200)
        mock_session_instance.get.return_value = mock_api_response

        # Call _api_request
        response_data = self.client._api_request(url, method="GET")

        # Verify the result
        self.assertEqual(response_data, {"items": [1, 2, 3]})
        mock_session_instance.get.assert_called_once_with(
            url,
            params=None,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Origin": "https://fogis.svenskfotboll.se",
                "Referer": f"{FogisApiClient.BASE_URL}/",
                "X-Requested-With": "XMLHttpRequest",
                "Cookie": "FogisMobilDomarKlient.ASPXAUTH=mock_auth_cookie",
            },
        )

    def test_api_request_http_error(self):
        """Unit test for _api_request handling HTTP errors."""
        # Mock the session's post method
        mock_session_instance = self.client.session
        url = f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SomeEndpoint"
        payload = {"param1": "value1"}

        # Create a mock response that raises an HTTP error
        mock_api_response = MockResponse({"error": "Not found"}, 404)
        mock_session_instance.post.return_value = mock_api_response
        mock_api_response.raise_for_status = MagicMock(side_effect=requests.exceptions.HTTPError("HTTP Error 404"))

        # Call _api_request and expect an exception
        with self.assertRaises(FogisAPIRequestError) as excinfo:
            self.client._api_request(url, payload, method="POST")

        self.assertIn("API request failed", str(excinfo.exception))
        mock_session_instance.post.assert_called_once_with(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Origin": "https://fogis.svenskfotboll.se",
                "Referer": f"{FogisApiClient.BASE_URL}/",
                "X-Requested-With": "XMLHttpRequest",
                "Cookie": "FogisMobilDomarKlient.ASPXAUTH=mock_auth_cookie",
            },
        )

    def test_api_request_invalid_json_response(self):
        """Unit test for _api_request handling invalid JSON response (missing 'd')."""
        # Mock the session's post method
        mock_session_instance = self.client.session
        url = f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SomeEndpoint"
        payload = {"param1": "value1"}

        # Create a mock response with invalid JSON (no 'd' key)
        mock_api_response = MockResponse({"not_d": "some_value"}, 200)
        mock_session_instance.post.return_value = mock_api_response

        # Call _api_request and expect the response to be returned as is
        response_data = self.client._api_request(url, payload, method="POST")

        # Verify the result
        self.assertEqual(response_data, {"not_d": "some_value"})

        mock_session_instance.post.assert_called_once_with(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Origin": "https://fogis.svenskfotboll.se",
                "Referer": f"{FogisApiClient.BASE_URL}/",
                "X-Requested-With": "XMLHttpRequest",
                "Cookie": "FogisMobilDomarKlient.ASPXAUTH=mock_auth_cookie",
            },
        )

    def test_fetch_matches_list_json_success(self):
        """Unit test for fetch_matches_list_json success."""
        # Mock the _api_request method
        self.client._api_request = MagicMock(return_value={"matchlista": [{"matchid": 1}, {"matchid": 2}]})

        # Call fetch_matches_list_json
        matches_list = self.client.fetch_matches_list_json()

        # Verify the result
        self.assertEqual(matches_list, [{"matchid": 1}, {"matchid": 2}])

        # Verify the API call was made once with the correct endpoint
        self.assertEqual(self.client._api_request.call_count, 1)
        call_args = self.client._api_request.call_args[0]
        self.assertEqual(
            call_args[0],
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatcherAttRapportera",
        )

        # Verify the filter structure without checking exact date values
        filter_data = call_args[1]["filter"]
        self.assertIn("datumFran", filter_data)
        self.assertIn("datumTill", filter_data)
        self.assertEqual(filter_data["datumTyp"], 0)
        self.assertEqual(filter_data["typ"], "alla")
        self.assertEqual(filter_data["status"], ["avbruten", "uppskjuten", "installd"])
        self.assertEqual(filter_data["alderskategori"], [1, 2, 3, 4, 5])
        self.assertEqual(filter_data["kon"], [3, 2, 4])
        self.assertIn("sparadDatum", filter_data)

    def test_fetch_matches_list_json_call_args(self):
        """Unit test for fetch_matches_list_json argument verification."""
        # Mock the _api_request method
        self.client._api_request = MagicMock(return_value={"matchlista": []})

        # Call fetch_matches_list_json
        self.client.fetch_matches_list_json()

        # Verify the API call was made once with the correct endpoint
        self.assertEqual(self.client._api_request.call_count, 1)
        call_args = self.client._api_request.call_args[0]
        self.assertEqual(
            call_args[0],
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatcherAttRapportera",
        )

        # Verify the filter structure without checking exact date values
        filter_data = call_args[1]["filter"]
        self.assertIn("datumFran", filter_data)
        self.assertIn("datumTill", filter_data)
        self.assertEqual(filter_data["datumTyp"], 0)
        self.assertEqual(filter_data["typ"], "alla")
        self.assertEqual(filter_data["status"], ["avbruten", "uppskjuten", "installd"])
        self.assertEqual(filter_data["alderskategori"], [1, 2, 3, 4, 5])
        self.assertEqual(filter_data["kon"], [3, 2, 4])
        self.assertIn("sparadDatum", filter_data)

    def test_fetch_matches_list_json_api_call_only(self):
        """Unit test for fetch_matches_list_json verifying API call (no filtering)."""
        # Mock the _api_request method
        self.client._api_request = MagicMock(return_value={"matchlista": []})

        # Call fetch_matches_list_json WITHOUT filter argument
        self.client.fetch_matches_list_json()

        # Verify the API call was made once with the correct endpoint
        self.assertEqual(self.client._api_request.call_count, 1)
        call_args = self.client._api_request.call_args[0]
        self.assertEqual(
            call_args[0],
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatcherAttRapportera",
        )

        # Verify the filter structure without checking exact date values
        filter_data = call_args[1]["filter"]
        self.assertIn("datumFran", filter_data)
        self.assertIn("datumTill", filter_data)
        self.assertEqual(filter_data["datumTyp"], 0)
        self.assertEqual(filter_data["typ"], "alla")
        self.assertEqual(filter_data["status"], ["avbruten", "uppskjuten", "installd"])
        self.assertEqual(filter_data["alderskategori"], [1, 2, 3, 4, 5])
        self.assertEqual(filter_data["kon"], [3, 2, 4])
        self.assertIn("sparadDatum", filter_data)

    def test_fetch_matches_list_json_server_date_filter_call_args(self):
        """Test fetch_matches_list_json with server-side date filter arguments."""
        # Mock the _api_request method
        self.client._api_request = MagicMock(return_value={"matchlista": []})

        # Call fetch_matches_list_json with filter
        custom_filter = {
            "datumFran": "2023-01-01",
            "datumTill": "2023-01-31",
            "datumTyp": "match",
            "sparadDatum": "2023-01-15",
        }
        self.client.fetch_matches_list_json(filter=custom_filter)

        # Verify the API call was made once with the correct endpoint
        self.assertEqual(self.client._api_request.call_count, 1)
        call_args = self.client._api_request.call_args[0]
        self.assertEqual(
            call_args[0],
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatcherAttRapportera",
        )

        # Verify the filter structure with our custom values
        filter_data = call_args[1]["filter"]
        self.assertEqual(filter_data["datumFran"], "2023-01-01")
        self.assertEqual(filter_data["datumTill"], "2023-01-31")
        self.assertEqual(filter_data["datumTyp"], "match")
        self.assertEqual(filter_data["sparadDatum"], "2023-01-15")

        # Verify the default values are still present
        self.assertEqual(filter_data["typ"], "alla")
        self.assertEqual(filter_data["status"], ["avbruten", "uppskjuten", "installd"])
        self.assertEqual(filter_data["alderskategori"], [1, 2, 3, 4, 5])
        self.assertEqual(filter_data["kon"], [3, 2, 4])

    def test_fetch_match_result_json(self):
        """Unit test for fetch_match_result_json method."""
        # Mock the _api_request method
        self.client._api_request = MagicMock(return_value=[{"matchresultattypid": 1, "matchlag1mal": 2, "matchlag2mal": 1}])

        # Call fetch_match_result_json
        match_id = 12345
        result_data = self.client.fetch_match_result_json(match_id)

        # Verify the result
        self.assertIsInstance(result_data, list)
        self.assertEqual(len(result_data), 1)
        self.assertEqual(result_data[0]["matchlag1mal"], 2)
        self.assertEqual(result_data[0]["matchlag2mal"], 1)

        # Verify the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatchresultatlista",
            {"matchid": 12345},
        )

    def test_fetch_match_result_json_error(self):
        """Unit test for fetch_match_result_json method with error."""
        # Mock the _api_request method to raise an exception
        error_msg = "API request failed"
        self.client._api_request = MagicMock(side_effect=FogisAPIRequestError(error_msg))

        # Call fetch_match_result_json and expect an exception
        with self.assertRaises(FogisAPIRequestError) as excinfo:
            self.client.fetch_match_result_json(12345)

        # Verify the exception message
        self.assertIn("API request failed", str(excinfo.exception))

        # Verify the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/GetMatchresultatlista",
            {"matchid": 12345},
        )

    def test_report_match_result(self):
        """Unit test for report_match_result method."""
        # Mock the _api_request method
        self.client._api_request = MagicMock(return_value={"success": True})

        # Call report_match_result
        result_data = {
            "matchid": 12345,  # Using integer instead of string
            "hemmamal": 2,
            "bortamal": 1,
            "halvtidHemmamal": 1,
            "halvtidBortamal": 0,
        }
        response = self.client.report_match_result(result_data)

        # Verify the result
        self.assertEqual(response, {"success": True})

        # Verify the API call - now using the nested structure
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchresultatLista",
            {
                "matchresultatListaJSON": [
                    {
                        "matchid": 12345,  # Should be converted to int
                        "matchresultattypid": 1,  # Full time
                        "matchlag1mal": 2,
                        "matchlag2mal": 1,
                        "wo": False,
                        "ow": False,
                        "ww": False
                    },
                    {
                        "matchid": 12345,
                        "matchresultattypid": 2,  # Half-time
                        "matchlag1mal": 1,
                        "matchlag2mal": 0,
                        "wo": False,
                        "ow": False,
                        "ww": False
                    }
                ]
            },
        )

    def test_report_match_result_error(self):
        """Unit test for report_match_result method with error."""
        # Mock the _api_request method to raise an exception
        error_msg = "API request failed"
        self.client._api_request = MagicMock(side_effect=FogisAPIRequestError(error_msg))

        # Call report_match_result and expect an exception
        result_data = {"matchid": 12345, "hemmamal": 2, "bortamal": 1}  # Using integer instead of string
        with self.assertRaises(FogisAPIRequestError) as excinfo:
            self.client.report_match_result(result_data)

        # Verify the exception message
        self.assertIn("API request failed", str(excinfo.exception))

        # Verify the API call - now using the nested structure
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchresultatLista",
            {
                "matchresultatListaJSON": [
                    {
                        "matchid": 12345,  # Should be converted to int
                        "matchresultattypid": 1,  # Full time
                        "matchlag1mal": 2,
                        "matchlag2mal": 1,
                        "wo": False,
                        "ow": False,
                        "ww": False
                    },
                    {
                        "matchid": 12345,
                        "matchresultattypid": 2,  # Half-time
                        "matchlag1mal": 0,
                        "matchlag2mal": 0,
                        "wo": False,
                        "ow": False,
                        "ww": False
                    }
                ]
            },
        )

    def test_event_types_dictionary(self):
        """Test that the event_types dictionary is present and properly formatted."""
        from fogis_api_client.event_types import EVENT_TYPES

        # Check that EVENT_TYPES is a dictionary
        self.assertIsInstance(EVENT_TYPES, dict)

        # Check that it has the expected keys and structure
        self.assertIn(6, EVENT_TYPES)  # Regular Goal
        self.assertIn(20, EVENT_TYPES)  # Yellow Card
        self.assertIn(17, EVENT_TYPES)  # Substitution

        # Check the structure of an entry
        self.assertIn("name", EVENT_TYPES[6])
        self.assertIn("goal", EVENT_TYPES[6])
        self.assertEqual(EVENT_TYPES[6]["name"], "Regular Goal")
        self.assertTrue(EVENT_TYPES[6]["goal"])

        # Check a non-goal event
        self.assertFalse(EVENT_TYPES[20]["goal"])

        # Check a control event
        self.assertIn("control_event", EVENT_TYPES[31])
        self.assertTrue(EVENT_TYPES[31]["control_event"])

    def test_report_team_official_action(self):
        """Unit test for report_team_official_action method."""
        # Mock the _api_request method
        self.client._api_request = MagicMock(return_value={"success": True})

        # Call report_team_official_action
        action_data = {
            "matchid": "12345",
            "lagid": "67890",  # Note: This parameter name is still 'lagid' in this method
            "personid": "54321",
            "matchlagledaretypid": "2",  # Example: Yellow card
            "minut": 65,
        }
        response = self.client.report_team_official_action(action_data)

        # Verify the result
        self.assertEqual(response, {"success": True})

        # Verify the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchlagledare",
            {
                "matchid": 12345,  # Should be converted to int
                # Note: This parameter name is still 'lagid' in this method
                "lagid": 67890,  # Should be converted to int
                "personid": 54321,  # Should be converted to int
                "matchlagledaretypid": 2,  # Should be converted to int
                "minut": 65,
            },
        )

    def test_report_team_official_action_error(self):
        """Unit test for report_team_official_action method with error."""
        # Mock the _api_request method to raise an exception
        error_msg = "API request failed"
        self.client._api_request = MagicMock(side_effect=FogisAPIRequestError(error_msg))

        # Call report_team_official_action and expect an exception
        action_data = {
            "matchid": "12345",
            "lagid": "67890",  # Note: This parameter name is still 'lagid' in this method
            "personid": "54321",
            "matchlagledaretypid": "2",
        }
        with self.assertRaises(FogisAPIRequestError) as excinfo:
            self.client.report_team_official_action(action_data)

        # Verify the exception message
        self.assertIn("API request failed", str(excinfo.exception))

        # Verify the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchlagledare",
            {
                "matchid": 12345,  # Should be converted to int
                # Note: This parameter name is still 'lagid' in this method
                "lagid": 67890,  # Should be converted to int
                "personid": 54321,  # Should be converted to int
                "matchlagledaretypid": 2,  # Should be converted to int
            },
        )

    def test_save_match_participant(self):
        """Unit test for save_match_participant method."""
        # Mock the _api_request method with a roster response
        mock_response = {
            "spelare": [
                {
                    "matchdeltagareid": 46123762,
                    "fornamn": "John",
                    "efternamn": "Doe",
                    "trojnummer": 92,
                    "lagkapten": False,
                    "ersattare": False,
                },
                {
                    "matchdeltagareid": 46123763,
                    "fornamn": "Jane",
                    "efternamn": "Smith",
                    "trojnummer": 10,
                    "lagkapten": True,
                    "ersattare": False,
                },
            ]
        }
        self.client._api_request = MagicMock(return_value=mock_response)

        # Call save_match_participant
        participant_data = {
            "matchdeltagareid": "46123762",
            "trojnummer": "92",
            "lagdelid": "0",
            "lagkapten": "false",
            "ersattare": "false",
            "positionsnummerhv": "0",
            "arSpelandeLedare": "false",
            "ansvarig": "false",
        }
        response = self.client.save_match_participant(participant_data)

        # Verify the result structure
        self.assertTrue(response["success"])
        self.assertTrue(response["verified"])
        self.assertEqual(response["roster"], mock_response)
        self.assertEqual(response["updated_player"]["matchdeltagareid"], 46123762)
        self.assertEqual(response["updated_player"]["trojnummer"], 92)
        self.assertEqual(response["updated_player"]["lagkapten"], False)

        # Verify the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchdeltagare",
            {
                "matchdeltagareid": 46123762,  # Should be converted to int
                "trojnummer": 92,  # Should be converted to int
                "lagdelid": 0,  # Should be converted to int
                "lagkapten": False,  # Should be converted to bool
                "ersattare": False,  # Should be converted to bool
                "positionsnummerhv": 0,  # Should be converted to int
                "arSpelandeLedare": False,  # Should be converted to bool
                "ansvarig": False,  # Should be converted to bool
            },
        )

    def test_save_match_participant_error(self):
        """Unit test for save_match_participant method with error."""
        # Mock the _api_request method to raise an exception
        error_msg = "API request failed"
        self.client._api_request = MagicMock(side_effect=FogisAPIRequestError(error_msg))

        # Call save_match_participant and expect an exception
        participant_data = {
            "matchdeltagareid": "46123762",
            "trojnummer": "92",
            "lagdelid": "0",
            "lagkapten": "false",
            "ersattare": "false",
            "positionsnummerhv": "0",
            "arSpelandeLedare": "false",
            "ansvarig": "false",
        }
        with self.assertRaises(FogisAPIRequestError) as excinfo:
            self.client.save_match_participant(participant_data)

        # Verify the exception message
        self.assertIn("API request failed", str(excinfo.exception))

        # Verify the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchdeltagare",
            {
                "matchdeltagareid": 46123762,  # Should be converted to int
                "trojnummer": 92,  # Should be converted to int
                "lagdelid": 0,  # Should be converted to int
                "lagkapten": False,  # Should be converted to bool
                "ersattare": False,  # Should be converted to bool
                "positionsnummerhv": 0,  # Should be converted to int
                "arSpelandeLedare": False,  # Should be converted to bool
                "ansvarig": False,  # Should be converted to bool
            },
        )

    def test_save_match_participant_verification_failure(self):
        """Unit test for save_match_participant method with verification failure."""
        # Mock the _api_request method with a roster response where values don't match
        mock_response = {
            "spelare": [
                {
                    "matchdeltagareid": 46123762,
                    "fornamn": "John",
                    "efternamn": "Doe",
                    "trojnummer": 7,  # Different from what we requested (92)
                    "lagkapten": False,
                    "ersattare": False,
                }
            ]
        }
        self.client._api_request = MagicMock(return_value=mock_response)

        # Call save_match_participant
        participant_data = {
            "matchdeltagareid": "46123762",
            "trojnummer": "92",
            "lagdelid": "0",
            "lagkapten": "false",
            "ersattare": "false",
            "positionsnummerhv": "0",
            "arSpelandeLedare": "false",
            "ansvarig": "false",
        }
        response = self.client.save_match_participant(participant_data)

        # Verify the result structure
        self.assertTrue(response["success"])  # API call succeeded
        self.assertFalse(response["verified"])  # But verification failed
        self.assertEqual(response["roster"], mock_response)
        self.assertEqual(response["updated_player"]["matchdeltagareid"], 46123762)
        self.assertEqual(response["updated_player"]["trojnummer"], 7)  # Not what we requested

        # Verify the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchdeltagare",
            {
                "matchdeltagareid": 46123762,
                "trojnummer": 92,
                "lagdelid": 0,
                "lagkapten": False,
                "ersattare": False,
                "positionsnummerhv": 0,
                "arSpelandeLedare": False,
                "ansvarig": False,
            },
        )

    def test_save_match_participant_spelareid_fallback(self):
        """Unit test for save_match_participant method with spelareid instead of matchdeltagareid."""
        # Mock the _api_request method with a roster response that uses spelareid instead of matchdeltagareid
        mock_response = {
            "spelare": [
                {
                    "spelareid": 12345,  # Different ID field (spelareid instead of matchdeltagareid)
                    "fornamn": "John",
                    "efternamn": "Doe",
                    "trojnummer": 92,  # Same jersey number as requested
                    "lagkapten": False,
                    "ersattare": False,
                }
            ]
        }
        self.client._api_request = MagicMock(return_value=mock_response)

        # Call save_match_participant
        participant_data = {
            "matchdeltagareid": "46123762",  # This ID won't be found in the response
            "trojnummer": "92",  # But this jersey number will match
            "lagdelid": "0",
            "lagkapten": "false",
            "ersattare": "false",
            "positionsnummerhv": "0",
            "arSpelandeLedare": "false",
            "ansvarig": "false",
        }
        response = self.client.save_match_participant(participant_data)

        # Verify the result structure
        self.assertTrue(response["success"])  # API call succeeded
        self.assertTrue(response["verified"])  # Verification should succeed based on jersey number
        self.assertEqual(response["roster"], mock_response)
        self.assertEqual(response["updated_player"]["trojnummer"], 92)  # Jersey number matches

        # Verify the API call
        self.client._api_request.assert_called_once_with(
            f"{FogisApiClient.BASE_URL}/MatchWebMetoder.aspx/SparaMatchdeltagare",
            {
                "matchdeltagareid": 46123762,
                "trojnummer": 92,
                "lagdelid": 0,
                "lagkapten": False,
                "ersattare": False,
                "positionsnummerhv": 0,
                "arSpelandeLedare": False,
                "ansvarig": False,
            },
        )


if __name__ == "__main__":
    unittest.main()
