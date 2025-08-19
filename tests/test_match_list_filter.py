import unittest
from typing import Any, Dict, List

from fogis_api_client.enums import AgeCategory, FootballType, Gender, MatchStatus
from fogis_api_client.match_list_filter import MatchListFilter


# --- Synthetic Data Generation (Adapt to your actual data structure and Enum values) ---
def create_test_matches(num_matches=10) -> List[Dict[str, Any]]:
    """Generates a list of synthetic match dictionaries for testing MatchListFilter."""
    statuses = [
        MatchStatus.CANCELLED,
        MatchStatus.POSTPONED,
        MatchStatus.INTERRUPTED,
        MatchStatus.COMPLETED,
        MatchStatus.NOT_STARTED,
    ]
    age_categories = [
        AgeCategory.CHILDREN,
        AgeCategory.YOUTH,
        AgeCategory.SENIOR,
        AgeCategory.VETERANS,
        AgeCategory.UNDEFINED,
    ]
    genders = [Gender.MALE, Gender.FEMALE, Gender.MIXED]
    football_types = [FootballType.FOOTBALL, FootballType.FUTSAL]

    matches = []
    for i in range(num_matches):
        match = {
            "matchid": 1000 + i,
            "installd": statuses[i % len(statuses)] == MatchStatus.CANCELLED,
            "avbruten": statuses[i % len(statuses)] == MatchStatus.INTERRUPTED,
            "uppskjuten": statuses[i % len(statuses)] == MatchStatus.POSTPONED,
            "arslutresultat": statuses[i % len(statuses)] == MatchStatus.COMPLETED,
            "tavlingAlderskategori": age_categories[i % len(age_categories)].value,
            "tavlingKonId": genders[i % len(genders)].value,
            "fotbollstypid": football_types[i % len(football_types)].value,
        }
        matches.append(match)
    return matches


class TestMatchListFilter(unittest.TestCase):
    def setUp(self):
        self.test_matches = create_test_matches(num_matches=20)  # Create a larger, more diverse dataset

    def _assert_filtered_statuses(self, filtered_matches, expected_statuses, exclude=False):
        """Helper assertion to check statuses of filtered matches."""
        expected_status_values = set(status.value for status in expected_statuses)
        for match in filtered_matches:
            match_statuses = {
                "installd": match.get("installd", False),
                "avbruten": match.get("avbruten", False),
                "uppskjuten": match.get("uppskjuten", False),
                "arslutresultat": match.get("arslutresultat", False),  # Assuming arslutresultat implies completed
            }
            active_status = next(
                (status for status, active in match_statuses.items() if active), None
            )  # Get the active status
            if exclude:  # Exclusion check
                self.assertFalse(
                    active_status in expected_status_values,
                    f"Match {match.get('matchid')} has excluded status {active_status}",
                )
            else:  # Inclusion check
                self.assertTrue(
                    active_status in expected_status_values,
                    f"Match {match.get('matchid')} does not have expected status (inclusion)",
                )

    def _assert_filtered_categories(self, filtered_matches, expected_categories, exclude=False):
        """Helper assertion to check age categories of filtered matches."""
        expected_category_values = set(cat.value for cat in expected_categories)
        for match in filtered_matches:
            category = match.get("tavlingAlderskategori")
            if exclude:  # Exclusion check
                self.assertNotIn(
                    category,
                    expected_category_values,
                    f"Match {match.get('matchid')} has excluded category {category}",
                )
            else:  # Inclusion check
                self.assertIn(
                    category,
                    expected_category_values,
                    f"Match {match.get('matchid')} does not have expected category (inclusion)",
                )

    def _assert_filtered_genders(self, filtered_matches, expected_genders, exclude=False):
        """Helper assertion to check genders of filtered matches."""
        expected_gender_values = set(gender.value for gender in expected_genders)
        for match in filtered_matches:
            gender_id = match.get("tavlingKonId")
            if exclude:  # Exclusion check
                self.assertNotIn(
                    gender_id,
                    expected_gender_values,
                    f"Match {match.get('matchid')} has excluded gender {gender_id}",
                )
            else:  # Inclusion check
                self.assertIn(
                    gender_id,
                    expected_gender_values,
                    f"Match {match.get('matchid')} does not have expected gender (inclusion)",
                )

    def _assert_filtered_football_types(self, filtered_matches, expected_football_types, exclude=False):
        """Helper assertion to check football types of filtered matches."""
        expected_football_type_ids = set(ftype.value for ftype in expected_football_types)
        for match in filtered_matches:
            football_type_id = match.get("fotbollstypid")
            if exclude:  # Exclusion check
                self.assertNotIn(
                    football_type_id,
                    expected_football_type_ids,
                    f"Match {match.get('matchid')} has excluded type {football_type_id}",
                )
            else:  # Inclusion check
                self.assertIn(
                    football_type_id,
                    expected_football_type_ids,
                    f"Match {match.get('matchid')} missing expected type (inclusion)",
                )

    # --- Status Filter Tests ---

    def test_filter_include_cancelled_status(self):
        """Test including only cancelled matches."""
        match_filter = MatchListFilter().include_statuses([MatchStatus.CANCELLED])
        filtered_matches = match_filter.filter_matches(self.test_matches)
        self._assert_filtered_statuses(filtered_matches, [MatchStatus.CANCELLED])  # Use helper assertion

    def test_filter_exclude_cancelled_status(self):
        """Test excluding cancelled matches."""
        match_filter = MatchListFilter().exclude_statuses([MatchStatus.CANCELLED])
        filtered_matches = match_filter.filter_matches(self.test_matches)
        self._assert_filtered_statuses(
            filtered_matches, [MatchStatus.CANCELLED], exclude=True
        )  # Use helper assertion with exclude=True

    # --- Age Category Filter Tests ---
    def test_filter_include_youth_age_category(self):
        """Test including only youth age category matches."""
        match_filter = MatchListFilter().include_age_categories([AgeCategory.YOUTH])
        filtered_matches = match_filter.filter_matches(self.test_matches)
        self._assert_filtered_categories(filtered_matches, [AgeCategory.YOUTH])  # Use helper assertion

    def test_filter_exclude_youth_age_category(self):
        """Test excluding youth age category matches."""
        match_filter = MatchListFilter().exclude_age_categories([AgeCategory.YOUTH])
        filtered_matches = match_filter.filter_matches(self.test_matches)
        self._assert_filtered_categories(
            filtered_matches, [AgeCategory.YOUTH], exclude=True
        )  # Use helper assertion with exclude=True

    # --- Gender Filter Tests ---
    def test_filter_include_female_gender(self):
        """Test including only female gender matches."""
        match_filter = MatchListFilter().include_genders([Gender.FEMALE])
        filtered_matches = match_filter.filter_matches(self.test_matches)
        # Use helper assertion
        self._assert_filtered_genders(filtered_matches, [Gender.FEMALE])

    def test_filter_exclude_female_gender(self):
        """Test excluding female gender matches."""
        match_filter = MatchListFilter().exclude_genders([Gender.FEMALE])
        filtered_matches = match_filter.filter_matches(self.test_matches)
        self._assert_filtered_genders(
            filtered_matches, [Gender.FEMALE], exclude=True
        )  # Use helper assertion with exclude=True

    # --- Football Type Filter Tests ---
    def test_filter_include_futsal_football_type(self):
        """Test including only futsal football type matches."""
        match_filter = MatchListFilter().include_football_types([FootballType.FUTSAL])
        filtered_matches = match_filter.filter_matches(self.test_matches)
        self._assert_filtered_football_types(filtered_matches, [FootballType.FUTSAL])  # Use helper assertion

    def test_filter_exclude_futsal_football_type(self):
        """Test excluding futsal football type matches."""
        match_filter = MatchListFilter().exclude_football_types([FootballType.FUTSAL])
        filtered_matches = match_filter.filter_matches(self.test_matches)
        self._assert_filtered_football_types(
            filtered_matches, [FootballType.FUTSAL], exclude=True
        )  # Use helper assertion with exclude=True

    # --- Combined Filter Tests (Examples - Add More Combinations!) ---

    def test_filter_exclude_cancelled_and_include_youth_categories(self):
        """Test combining exclude status and include age category filters."""
        match_filter = MatchListFilter()
        filtered_matches = (
            match_filter.exclude_statuses([MatchStatus.CANCELLED])
            .include_age_categories([AgeCategory.YOUTH])
            .filter_matches(self.test_matches)
        )
        # --- Assert BOTH status and category filters are applied ---
        self._assert_filtered_statuses(filtered_matches, [MatchStatus.CANCELLED], exclude=True)
        self._assert_filtered_categories(filtered_matches, [AgeCategory.YOUTH])

    def test_filter_include_postponed_and_exclude_female_gender_futsal_type(self):
        """Test combining include status, exclude gender, and exclude football type filters."""
        match_filter = MatchListFilter()
        filtered_matches = (
            match_filter.include_statuses([MatchStatus.POSTPONED])
            .exclude_genders([Gender.FEMALE])
            .exclude_football_types([FootballType.FUTSAL])
            .filter_matches(self.test_matches)
        )
        # --- Assert ALL combined filters are applied ---
        self._assert_filtered_statuses(filtered_matches, [MatchStatus.POSTPONED])
        self._assert_filtered_genders(filtered_matches, [Gender.FEMALE], exclude=True)
        self._assert_filtered_football_types(filtered_matches, [FootballType.FUTSAL], exclude=True)

    def test_filter_no_filter_returns_all_matches(self):
        """Test that calling filter_matches with no filter criteria returns all matches."""
        match_filter = MatchListFilter()  # No filter configuration
        filtered_matches = match_filter.filter_matches(self.test_matches)
        self.assertEqual(
            filtered_matches,
            self.test_matches,
            "Expected all matches to be returned when no filter is applied.",
        )


if __name__ == "__main__":
    unittest.main()
