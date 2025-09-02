from typing import Any, Dict, List, Optional

from .enums import AgeCategory, FootballType, Gender, MatchStatus
from .fogis_api_client import FogisApiClient


class MatchListFilter:
    """
    A class for building and applying filters to lists of matches fetched from the Fogis API.

    This class combines filter configuration and application logic for both server-side
    and client-side filtering.
    It provides a fluent API (chainable methods) for building complex filter criteria
    and fetching filtered matches.
    """

    def __init__(self):
        """Initializes a new MatchListFilter instance with no filters applied by default."""
        self._status_include: Optional[List[MatchStatus]] = None
        self._status_exclude: Optional[List[MatchStatus]] = None
        self._alderskategori_exclude: Optional[List[AgeCategory]] = None
        self._alderskategori_include: Optional[List[AgeCategory]] = None
        self._kon_exclude: Optional[List[Gender]] = None
        self._kon_include: Optional[List[Gender]] = None
        self._fotbollstypid_exclude: Optional[List[FootballType]] = None
        self._fotbollstypid_include: Optional[List[FootballType]] = None

        # --- Date range filter (server-side)
        self._datum_fran: Optional[str] = None
        self._datum_till: Optional[str] = None

    # --- Builder methods (chainable configuration) ---

    def start_date(self, start_date: str) -> "MatchListFilter":
        """Sets the start date for server-side date range filtering."""
        self._datum_fran = start_date
        return self

    def end_date(self, end_date: str) -> "MatchListFilter":
        """Sets the end date for server-side date range filtering."""
        self._datum_till = end_date
        return self

    def date_range_type(self, date_range_type: int) -> "MatchListFilter":
        """Sets the date range type (0 for relative, 1 for fixed) for server-side filtering."""
        self._datum_typ = date_range_type
        return self

    def saved_datum(self, saved_datum: str) -> "MatchListFilter":
        """Sets the saved date for filter (included for completeness)."""
        self._sparad_datum = saved_datum
        return self

    def include_statuses(self, statuses: List[MatchStatus]) -> "MatchListFilter":
        """Includes matches with any of the specified statuses in the filter."""
        self._status_include = statuses
        return self

    def exclude_statuses(self, statuses: List[MatchStatus]) -> "MatchListFilter":
        """Excludes matches with any of the specified statuses from the filter."""
        self._status_exclude = statuses
        return self

    def include_age_categories(self, age_categories: List[AgeCategory]) -> "MatchListFilter":
        """Includes matches with any of the specified age categories in the filter."""
        self._alderskategori_include = age_categories
        return self

    def exclude_age_categories(self, age_categories: List[AgeCategory]) -> "MatchListFilter":
        """Excludes matches with any of the specified age categories from the filter."""
        self._alderskategori_exclude = age_categories
        return self

    def include_genders(self, genders: List[Gender]) -> "MatchListFilter":
        """Includes matches with any of the specified genders in the filter."""
        self._kon_include = genders
        return self

    def exclude_genders(self, genders: List[Gender]) -> "MatchListFilter":
        """Excludes matches with any of the specified genders from the filter."""
        self._kon_exclude = genders
        return self

    def include_football_types(self, football_types: List[FootballType]) -> "MatchListFilter":
        """Includes matches with any of the specified football types in the filter."""
        self._fotbollstypid_include = football_types
        return self

    def exclude_football_types(self, football_types: List[FootballType]) -> "MatchListFilter":
        """Excludes matches with any of the specified football types from the filter."""
        self._fotbollstypid_exclude = football_types
        return self

    def build_payload(self) -> Dict[str, Any]:
        """Builds the MINIMAL filter payload dictionary.

        Includes ONLY server-side criteria that are actually configured.

        Date range, status, alderskategori, and kon filters are COMPLETELY OMITTED
        from the default server-side payload
        if they are not explicitly configured using the builder methods,
        for maximum efficiency and API clarity.
        """
        payload_filter: Dict[str, Any] = {}

        # --- Conditionally add date range filters to payload ONLY if configured ---
        if self._datum_fran:
            payload_filter["datumFran"] = self._datum_fran
        if self._datum_till:
            payload_filter["datumTill"] = self._datum_till

        # --- Conditionally add status, alderskategori, kon filters (same logic as before) ---
        if self._status_include or self._status_exclude:
            status_values: List[str] = []
            if self._status_include:
                status_values = [status.value for status in self._status_include]
            elif self._status_exclude:
                status_values = [status.value for status in self._status_exclude]
            payload_filter["status"] = status_values

        if self._alderskategori_include or self._alderskategori_exclude:
            age_category_values: List[int] = []
            if self._alderskategori_include:
                age_category_values = [cat.value for cat in self._alderskategori_include]
            elif self._alderskategori_exclude:
                age_category_values = [cat.value for cat in self._alderskategori_exclude]
            payload_filter["alderskategori"] = age_category_values

        if self._kon_include or self._kon_exclude:
            gender_values: List[int] = []
            if self._kon_include:
                gender_values = [gender.value for gender in self._kon_include]
            elif self._kon_exclude:
                gender_values = [gender.value for gender in self._kon_exclude]
            payload_filter["kon"] = gender_values

        return payload_filter

    def filter_matches(self, matches: List[Any]) -> List[Any]:
        """Applies the configured client-side filters to the list of matches."""
        filtered_matches = list(matches)  # Create a copy to avoid modifying original list

        if self._status_include is not None:
            status_filter_values = set(status.value for status in self._status_include)
            filtered_matches = [
                match
                for match in filtered_matches
                if any(
                    [  # Inclusion logic for status
                        match.get("installd") and "installd" in status_filter_values,
                        match.get("avbruten") and "avbruten" in status_filter_values,
                        match.get("uppskjuten") and "uppskjuten" in status_filter_values,
                        match.get("arslutresultat") and "genomford" in status_filter_values,
                        # ... (add conditions for other statuses) ...
                    ]
                )
            ]
        if self._status_exclude is not None:
            status_filter_values = set(status.value for status in self._status_exclude)  # Use .value for Enum
            filtered_matches = [
                match
                for match in filtered_matches
                if not (  # Exclusion logic for status
                    ("installd" in status_filter_values and match.get("installd", False))
                    or ("avbruten" in status_filter_values and match.get("avbruten", False))
                    or ("uppskjuten" in status_filter_values and match.get("uppskjuten", False))
                    # ... (add conditions for other statuses) ...
                )
            ]

        if self._alderskategori_include is not None:
            allowed_categories = set(cat.value for cat in self._alderskategori_include)  # Use .value for Enum
            filtered_matches = [
                match
                for match in filtered_matches
                if match.get("tavlingAlderskategori") in allowed_categories  # Inclusion logic
            ]
        if self._alderskategori_exclude is not None:
            excluded_categories = set(cat.value for cat in self._alderskategori_exclude)  # Use .value for Enum
            filtered_matches = [
                match
                for match in filtered_matches
                if match.get("tavlingAlderskategori") not in excluded_categories  # Exclusion logic
            ]

        if self._kon_include is not None:
            allowed_genders = set(gender.value for gender in self._kon_include)  # Use .value for Enum
            filtered_matches = [
                match for match in filtered_matches if match.get("tavlingKonId") in allowed_genders  # Inclusion logic
            ]
        if self._kon_exclude is not None:
            excluded_genders = set(gender.value for gender in self._kon_exclude)  # Use .value for Enum
            filtered_matches = [
                match for match in filtered_matches if match.get("tavlingKonId") not in excluded_genders  # Exclusion logic
            ]

        if self._fotbollstypid_include is not None:
            allowed_football_types = set(ftype.value for ftype in self._fotbollstypid_include)  # Use .value for Enum
            filtered_matches = [
                match for match in filtered_matches if match.get("fotbollstypid") in allowed_football_types  # Inclusion logic
            ]
        if self._fotbollstypid_exclude is not None:
            excluded_football_types = set(ftype.value for ftype in self._fotbollstypid_exclude)  # Use .value for Enum
            filtered_matches = [
                match
                for match in filtered_matches
                if match.get("fotbollstypid") not in excluded_football_types  # Exclusion logic
            ]

        return filtered_matches

    def fetch_filtered_matches(self, api_client: FogisApiClient) -> List[Dict[str, Any]]:
        """
        Fetches matches from the API using FogisApiClient and applies the configured filters.

        This method uses server-side filtering when possible for better performance,
        and falls back to client-side filtering if server-side filtering fails.

        Args:
            api_client: An instance of FogisApiClient to use for fetching matches.

        Returns:
            A list of match dictionaries, filtered according to the configured criteria.

        Raises:
            FogisAPIRequestError: If the API request fails and fallback is not possible.
            FogisDataError: If the response data is invalid.
        """
        payload_filter = self.build_payload()  # Build server-side payload

        try:
            # Use the correct parameter name for PublicApiClient
            response = api_client.fetch_matches_list_json(
                filter_params=payload_filter
            )  # Fetch using API client and server-side filters

            # Extract matches from response - handle different response formats
            all_matches = []
            if response is None:
                return []
            elif isinstance(response, list):
                all_matches = response
            elif isinstance(response, dict):
                if "matchlista" in response:
                    all_matches = response["matchlista"]
                else:
                    # If response is a dict but doesn't have matchlista, treat as single match
                    all_matches = [response] if response else []
            else:
                # Unexpected response format
                return []

        except Exception as e:
            # Fallback to basic fetch if server-side filtering fails
            try:
                basic_response = api_client.fetch_matches_list_json()
                if isinstance(basic_response, list):
                    all_matches = basic_response
                elif isinstance(basic_response, dict) and "matchlista" in basic_response:
                    all_matches = basic_response["matchlista"]
                else:
                    all_matches = []
            except Exception:
                # If both server-side and fallback fail, re-raise the original exception
                raise e

        # Apply client-side filtering to the results
        filtered_matches = self.filter_matches(all_matches)
        return filtered_matches
