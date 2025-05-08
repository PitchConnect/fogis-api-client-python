#!/usr/bin/env python3
"""
Script to update all test methods in test_with_mock_server.py to use the new base URL pattern.
"""
import re

# Read the file
with open("integration_tests/test_with_mock_server.py", "r") as f:
    content = f.read()

# Define the patterns
old_pattern = r'(\s+)# Override the base URL to use the mock server\n\s+FogisApiClient\.BASE_URL = f"{mock_fogis_server\[\'base_url\'\]}/mdk"'
new_pattern = r'\1# Override the base URL to use the mock server\n\1original_base_url = FogisApiClient.BASE_URL\n\1FogisApiClient.BASE_URL = f"{mock_fogis_server[\'base_url\']}/mdk"\n\n\1# Also override the internal API client\'s base URL\n\1from fogis_api_client.internal.api_client import InternalApiClient\n\1original_internal_base_url = InternalApiClient.BASE_URL\n\1InternalApiClient.BASE_URL = f"{mock_fogis_server[\'base_url\']}/mdk"'

# Replace all occurrences
updated_content = re.sub(old_pattern, new_pattern, content)

# Define the teardown pattern
teardown_pattern = r'(\s+)(assert .+?\n)(?=\n\s+def test_|$)'
teardown_replacement = r'\1\2\n\1# Restore the original base URLs\n\1FogisApiClient.BASE_URL = original_base_url\n\1InternalApiClient.BASE_URL = original_internal_base_url'

# Replace all occurrences of the teardown pattern
updated_content = re.sub(teardown_pattern, teardown_replacement, updated_content)

# Write the updated content back to the file
with open("integration_tests/test_with_mock_server.py", "w") as f:
    f.write(updated_content)

print("Updated all test methods in test_with_mock_server.py")
