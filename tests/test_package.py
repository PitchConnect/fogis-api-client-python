import fogis_api_client


def test_version_is_exposed() -> None:
    assert fogis_api_client.__version__.startswith("1.")
