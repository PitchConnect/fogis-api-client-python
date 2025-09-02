import unittest
from unittest.mock import MagicMock, patch

from fogis_api_client.cookies import (
    PUBLIC_AUTH,
    PUBLIC_SESSION,
    SERVER_AUTH,
    SERVER_SESSION,
    normalize_public_cookie_keys,
    to_server_cookie_keys,
)


class TestCookieNormalization(unittest.TestCase):
    def test_normalize_from_server_keys(self):
        raw = {SERVER_AUTH: "a", SERVER_SESSION: "b"}
        out = normalize_public_cookie_keys(raw)
        self.assertEqual(out[PUBLIC_AUTH], "a")
        self.assertEqual(out[PUBLIC_SESSION], "b")

    def test_normalize_from_public_keys(self):
        raw = {PUBLIC_AUTH: "x", PUBLIC_SESSION: "y"}
        out = normalize_public_cookie_keys(raw)
        self.assertEqual(out[PUBLIC_AUTH], "x")
        self.assertEqual(out[PUBLIC_SESSION], "y")

    def test_to_server_keys_from_public(self):
        pub = {PUBLIC_AUTH: "1", PUBLIC_SESSION: "2"}
        out = to_server_cookie_keys(pub)
        self.assertEqual(out[SERVER_AUTH], "1")
        self.assertEqual(out[SERVER_SESSION], "2")

    def test_to_server_keys_from_mixed(self):
        mixed = {PUBLIC_AUTH: "p", SERVER_SESSION: "s"}
        out = to_server_cookie_keys(mixed)
        self.assertEqual(out[SERVER_AUTH], "p")
        self.assertEqual(out[SERVER_SESSION], "s")
