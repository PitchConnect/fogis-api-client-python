"""
Factory for generating sample data for the mock FOGIS API server.

This module provides a factory class that can generate various types of sample data
that mimic the responses from the FOGIS API, with proper structure but anonymized content.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union


class MockDataFactory:
    """Factory for generating sample data for the mock FOGIS API server."""

    @staticmethod
    def generate_id() -> int:
        """Generate a random ID."""
        return random.randint(1000000, 9999999)

    @staticmethod
    def generate_match_number() -> str:
        """Generate a random match number."""
        return f"{random.randint(0, 999999):06d}"

    @staticmethod
    def generate_name(first_name: bool = True) -> str:
        """Generate a random name."""
        if first_name:
            names = [
                "John",
                "Jane",
                "Alex",
                "Sam",
                "Chris",
                "Pat",
                "Taylor",
                "Morgan",
                "Jordan",
                "Casey",
            ]
            return random.choice(names)
        else:
            surnames = [
                "Smith",
                "Johnson",
                "Williams",
                "Brown",
                "Jones",
                "Miller",
                "Davis",
                "Garcia",
                "Rodriguez",
                "Wilson",
            ]
            return random.choice(surnames)

    @staticmethod
    def generate_full_name() -> str:
        """Generate a random full name."""
        return f"{MockDataFactory.generate_name(True)} {MockDataFactory.generate_name(False)}"

    @staticmethod
    def generate_team_name() -> str:
        """Generate a random team name."""
        prefixes = [
            "FC",
            "United",
            "City",
            "Athletic",
            "Sporting",
            "Real",
            "Inter",
            "Dynamo",
        ]
        locations = [
            "North",
            "South",
            "East",
            "West",
            "Central",
            "Metro",
            "Royal",
            "Olympic",
        ]
        return f"{random.choice(locations)} {random.choice(prefixes)}"

    @staticmethod
    def generate_phone() -> str:
        """Generate a random phone number."""
        return f"07{random.randint(0, 9)}{random.randint(0, 9)}-{random.randint(100000, 999999)}"

    @staticmethod
    def generate_email(name: Optional[str] = None) -> str:
        """Generate a random email address."""
        if name is None:
            name = MockDataFactory.generate_full_name().lower().replace(" ", ".")
        domains = ["example.com", "test.org", "sample.net", "mock.io", "demo.se"]
        return f"{name}@{random.choice(domains)}"

    @staticmethod
    def generate_address() -> str:
        """Generate a random address."""
        streets = ["Main St", "Park Ave", "Oak Rd", "Maple Ln", "Cedar Blvd"]
        return f"{random.randint(1, 999)} {random.choice(streets)}"

    @staticmethod
    def generate_postal_code() -> str:
        """Generate a random postal code."""
        return f"{random.randint(10000, 99999)}"

    @staticmethod
    def generate_city() -> str:
        """Generate a random city name."""
        cities = [
            "Springfield",
            "Rivertown",
            "Lakeside",
            "Mountainview",
            "Valleyfield",
            "Brookhaven",
        ]
        return random.choice(cities)

    @staticmethod
    def generate_date(future: bool = True, days_offset: Optional[int] = None) -> str:
        """Generate a random date in YYYY-MM-DD format."""
        if days_offset is None:
            days_offset = random.randint(1, 180) if future else -random.randint(1, 180)

        date = datetime.now() + timedelta(days=days_offset)
        return date.strftime("%Y-%m-%d")

    @staticmethod
    def generate_time() -> str:
        """Generate a random time in HH:MM format."""
        hours = random.randint(10, 20)
        minutes = random.choice([0, 15, 30, 45])
        return f"{hours:02d}:{minutes:02d}"

    @staticmethod
    def generate_timestamp(future: bool = True, days_offset: Optional[int] = None) -> int:
        """Generate a random timestamp in milliseconds."""
        if days_offset is None:
            days_offset = random.randint(1, 180) if future else -random.randint(1, 180)

        date = datetime.now() + timedelta(days=days_offset)
        return int(date.timestamp() * 1000)

    @staticmethod
    def generate_formatted_timestamp(future: bool = True, days_offset: Optional[int] = None) -> str:
        """Generate a random timestamp in FOGIS format."""
        timestamp = MockDataFactory.generate_timestamp(future, days_offset)
        return f"\\/Date({timestamp})\\/"

    @staticmethod
    def generate_match_list(count: int = 5) -> Dict[str, Any]:
        """Generate a sample match list response."""
        matches = []

        for _ in range(count):
            match_id = MockDataFactory.generate_id()
            match_number = MockDataFactory.generate_match_number()
            home_team = MockDataFactory.generate_team_name()
            away_team = MockDataFactory.generate_team_name()
            competition = f"Division {random.randint(1, 5)}"
            match_date = MockDataFactory.generate_date(True)
            match_time = MockDataFactory.generate_time()

            # Generate referee information
            referees = []
            for role_id, role_name, role_short in [
                (1, "Huvuddomare", "Dom"),
                (2, "Assisterande 1", "AD1"),
                (3, "Assisterande 2", "AD2"),
            ]:
                referee_name = MockDataFactory.generate_full_name()
                referees.append(
                    {
                        "domaruppdragid": MockDataFactory.generate_id(),
                        "matchid": match_id,
                        "matchnr": match_number,
                        "domarrollid": role_id,
                        "domarrollnamn": role_name,
                        "domarrollkortnamn": role_short,
                        "domareid": MockDataFactory.generate_id(),
                        "domarnr": str(random.randint(10000, 99999)),
                        "personid": MockDataFactory.generate_id(),
                        "domaruppdragstatusid": 5,
                        "domaruppdragstatusnamn": "Tilldelat",
                        "personnamn": referee_name,
                        "telefon": "",
                        "mobiltelefon": MockDataFactory.generate_phone(),
                        "telefonarbete": "",
                        "adress": MockDataFactory.generate_address(),
                        "coadress": "",
                        "epostadress": MockDataFactory.generate_email(
                            referee_name.lower().replace(" ", ".")
                        ),
                        "land": "Sverige",
                        "namn": referee_name,
                        "postnr": MockDataFactory.generate_postal_code(),
                        "postort": MockDataFactory.generate_city(),
                    }
                )

            # Generate contact persons
            contacts = []
            for team_name in [home_team, away_team]:
                for is_reserve in [False, True]:
                    contact_name = MockDataFactory.generate_full_name()
                    contacts.append(
                        {
                            "lagid": MockDataFactory.generate_id(),
                            "lagnamn": f"{team_name}",
                            "personid": MockDataFactory.generate_id(),
                            "personnamn": contact_name,
                            "telefon": "",
                            "mobiltelefon": MockDataFactory.generate_phone(),
                            "telefonarbete": "",
                            "adress": MockDataFactory.generate_address(),
                            "coadress": "",
                            "epostadress": MockDataFactory.generate_email(
                                contact_name.lower().replace(" ", ".")
                            ),
                            "land": "Sverige",
                            "postnr": MockDataFactory.generate_postal_code(),
                            "postort": MockDataFactory.generate_city(),
                            "reserv": is_reserve,
                            "foreningId": MockDataFactory.generate_id(),
                        }
                    )

            # Create the match object
            match = {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchJSON",
                "value": match_number,
                "label": (
                    f"{match_number}: {home_team} - {away_team} ({competition}), "
                    f"{match_date} {match_time}"
                ),
                "matchid": match_id,
                "matchnr": match_number,
                "fotbollstypid": 1,
                "matchlag1id": MockDataFactory.generate_id(),
                "lag1lagengagemangid": MockDataFactory.generate_id(),
                "lag1lagid": MockDataFactory.generate_id(),
                "lag1foreningid": MockDataFactory.generate_id(),
                "lag1forbundid": 0,
                "lag1namn": home_team,
                "lag1spelsystem": "4-4-2",
                "matchlag2id": MockDataFactory.generate_id(),
                "lag2lagengagemangid": MockDataFactory.generate_id(),
                "lag2lagid": MockDataFactory.generate_id(),
                "lag2foreningid": MockDataFactory.generate_id(),
                "lag2forbundid": 0,
                "lag2namn": away_team,
                "lag2spelsystem": "4-3-3",
                "anlaggningid": MockDataFactory.generate_id(),
                "anlaggningnamn": (
                    f"{random.choice(['Arena', 'Stadium', 'Park'])} " f"{random.randint(1, 5)}"
                ),
                "anlaggningLatitud": round(57.0 + random.random(), 6),
                "anlaggningLongitud": round(12.0 + random.random(), 6),
                "tid": MockDataFactory.generate_formatted_timestamp(True),
                "speldatum": match_date,
                "avsparkstid": match_time,
                "tidsangivelse": f"{match_date}, {match_time}",
                "tavlingid": MockDataFactory.generate_id(),
                "tavlingnr": match_number[:6],
                "tavlingnamn": competition,
                "tavlingskategoriid": MockDataFactory.generate_id(),
                "tavlingskategorinamn": f"Division {random.randint(1, 5)}",
                "tavlingagsavforbundid": 1,
                "matchlag1mal": random.randint(0, 5),
                "matchlag2mal": random.randint(0, 5),
                "arslutresultat": random.choice([True, False]),
                "wo": False,
                "ow": False,
                "ww": False,
                "antalaskadare": random.randint(0, 2000),
                "uppskjuten": False,
                "avbruten": False,
                "installd": False,
                "matchrapportgodkandavdomare": random.choice([True, False]),
                "matchrapportgodkandavdomaredatum": (
                    MockDataFactory.generate_formatted_timestamp(False)
                    if random.choice([True, False])
                    else "\\/Date(-62135596800000)\\/"
                ),
                "matchrapportgodkandavdomaredatumformaterad": "",
                "tavlinganvanderhogupplosttid": False,
                "tavlingantalstartadespelareigodkanddomarrapport": 11,
                "tavlingmaxantalspelareimatchtruppigodkanddomarrapport": 18,
                "tavlingantalledareimatchtrupp": 7,
                "tavlingantalspelareimatchtrupp": 18,
                "antalhalvlekar": 2,
                "tidperhalvlek": 45,
                "antalforlangningsperioder": 0,
                "tidperforlangningsperiod": 0,
                "liverapporteringTillaten": True,
                "liverapporteringPaborjad": False,
                "liverapporteringAvslutad": False,
                "liverapporteringsAktorTypId": 2,
                "anvanderspelarleg": False,
                "foreningsanvandarefarredigeramotstandartrupp": True,
                "foreningsanvandarefarregistreramatchhandelser": False,
                "foreningsanvandarefarregistreramatchresultat": False,
                "domaruppdraglista": referees,
                "domarefargodkannarapport": True,
                "domarrapporteringTillaten": True,
                "noteringfranlag1": "",
                "noteringfranlag2": "",
                "noteringfrandomare": "",
                "tavlingFriaByten": False,
                "tavlingDomareMojliggorHamtningAvFrammandeSpelareTillMatchtrupp": True,
                "tavlingAntalTimmarInnanMatchForTruppAdministration": 45,
                # Require responsible team leader
                "tavlingDomareKravForekomstAvAnsvarigLagledareIGodkandDomarrapport": True,
                "tavlingAntalDagarEfterMatchForAdministrationAvDomarrapport": 3,
                "tavlingKonId": 2,
                "tavlingAlderskategori": 4,
                "kontaktpersoner": contacts,
                # Match squad publication time for home team
                "matchlag1OffentliggorMatchtruppDatumTid": (
                    MockDataFactory.generate_formatted_timestamp(True)
                ),
                # Match squad publication time for away team
                "matchlag2OffentliggorMatchtruppDatumTid": (
                    MockDataFactory.generate_formatted_timestamp(True)
                ),
                "tavlingDomareAntalMinuterForeMatchSomTrupperOffentliggors": 45,
                # Additional fields
                "domareArHuvuddomare": True,
                "tavlingMatchklimatDomareKanLamnaOmdome": False,
                # Match climate settings
                "tavlingDomareVisaVarningsOchAvstangningsAckumulering": True,
            }

            matches.append(match)

        # Create the full response structure
        response = {
            "d": {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatcherAttRapportera",
                "anvandartyp": "Domare",
                "anvandareforeningid": 0,
                "matchlista": matches,
                "anvandare": None,
                "endastLiverapportor": False,
            }
        }

        return response

    @staticmethod
    def generate_match_details(match_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate sample match details."""
        if match_id is None:
            match_id = MockDataFactory.generate_id()

        match_number = MockDataFactory.generate_match_number()
        home_team = MockDataFactory.generate_team_name()
        away_team = MockDataFactory.generate_team_name()
        match_date = MockDataFactory.generate_date(True)
        match_time = MockDataFactory.generate_time()

        match_details = {
            "matchid": match_id,
            "matchnr": match_number,
            "datum": match_date,
            "tid": match_time,
            "hemmalag": home_team,
            "bortalag": away_team,
            "hemmalagid": MockDataFactory.generate_id(),
            "bortalagid": MockDataFactory.generate_id(),
            "arena": f"{random.choice(['Arena', 'Stadium', 'Park'])} {random.randint(1, 5)}",
            "status": "Fastställd",
            "domare": MockDataFactory.generate_full_name(),
            "ad1": MockDataFactory.generate_full_name(),
            "ad2": MockDataFactory.generate_full_name(),
            "fjarde": "",
            "matchtyp": "Serie",
            "tavling": f"Division {random.randint(1, 5)}",
            "grupp": f"Group {random.choice(['A', 'B', 'C', 'D'])}",
            "hemmamal": random.randint(0, 5),
            "bortamal": random.randint(0, 5),
            "publik": random.randint(100, 2000),
            "notering": "",
            "rapportstatus": "Ej påbörjad",
            "matchstart": None,
            "halvtidHemmamal": random.randint(0, 3),
            "halvtidBortamal": random.randint(0, 3),
        }

        return match_details

    @staticmethod
    def generate_match_players(
        match_id: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate sample match players based on real FOGIS API data structure."""
        if match_id is None:
            match_id = MockDataFactory.generate_id()

        # Generate home and away team IDs and names
        home_team_id = MockDataFactory.generate_id()
        away_team_id = MockDataFactory.generate_id()
        home_team_name = MockDataFactory.generate_team_name()
        away_team_name = MockDataFactory.generate_team_name()
        home_team_club_id = MockDataFactory.generate_id()
        away_team_club_id = MockDataFactory.generate_id()

        home_players = []
        away_players = []

        # Generate home team players
        for i in range(18):
            is_captain = i == 0
            is_substitute = i >= 11  # First 11 are starters, rest are substitutes
            jersey_number = i + 1

            # Generate a random Swedish personal number (YYYYMMDDXXXX)
            birth_year = random.randint(1990, 2005)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)  # Simplified to avoid invalid dates
            personal_number = (
                f"{birth_year}{birth_month:02d}{birth_day:02d}{random.randint(1000, 9999)}"
            )

            # Create player with the full structure from real data
            player = {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchdeltagareJSON",
                "matchdeltagareid": MockDataFactory.generate_id(),
                "matchid": match_id,
                "matchlagid": home_team_id,
                "spelareid": MockDataFactory.generate_id(),
                "trojnummer": jersey_number,
                "fornamn": MockDataFactory.generate_name(True),
                "efternamn": MockDataFactory.generate_name(False),
                "personnr": personal_number,
                "agerestriction": "",
                "matchlagnamn": home_team_name,
                "lagdelid": 0,
                "lagkapten": is_captain,
                "ersattare": is_substitute,
                "ejlicensieradibeslaktadforening": False,
                "foreningid": home_team_club_id,
                "positionsnummerhv": 0,
                "byte1": 0,  # Will be filled in for substituted players
                "byte2": 0,
                "utvisning": "",
                "arSpelandeLedare": False,
                "ansvarig": False,
                "spelarregistreringsstrang": "",
                "spelareAntalAckumuleradeVarningar": random.randint(0, 2),
                "spelareAvstangningBeskrivning": "",
            }

            home_players.append(player)

        # Generate away team players
        for i in range(18):
            is_captain = i == 0
            is_substitute = i >= 11  # First 11 are starters, rest are substitutes
            jersey_number = i + 1

            # Generate a random Swedish personal number (YYYYMMDDXXXX)
            birth_year = random.randint(1990, 2005)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)  # Simplified to avoid invalid dates
            personal_number = (
                f"{birth_year}{birth_month:02d}{birth_day:02d}{random.randint(1000, 9999)}"
            )

            # Create player with the full structure from real data
            player = {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchdeltagareJSON",
                "matchdeltagareid": MockDataFactory.generate_id(),
                "matchid": match_id,
                "matchlagid": away_team_id,
                "spelareid": MockDataFactory.generate_id(),
                "trojnummer": jersey_number,
                "fornamn": MockDataFactory.generate_name(True),
                "efternamn": MockDataFactory.generate_name(False),
                "personnr": personal_number,
                "agerestriction": "",
                "matchlagnamn": away_team_name,
                "lagdelid": 0,
                "lagkapten": is_captain,
                "ersattare": is_substitute,
                "ejlicensieradibeslaktadforening": False,
                "foreningid": away_team_club_id,
                "positionsnummerhv": 0,
                "byte1": 0,  # Will be filled in for substituted players
                "byte2": 0,
                "utvisning": "",
                "arSpelandeLedare": False,
                "ansvarig": False,
                "spelarregistreringsstrang": "",
                "spelareAntalAckumuleradeVarningar": random.randint(0, 2),
                "spelareAvstangningBeskrivning": "",
            }

            away_players.append(player)

        return {
            "hemmalag": home_players,
            "bortalag": away_players,
        }

    @staticmethod
    def generate_match_officials(
        match_id: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate sample match officials based on real FOGIS API data structure."""
        if match_id is None:
            match_id = MockDataFactory.generate_id()

        # Generate home and away team IDs and names
        home_team_id = MockDataFactory.generate_id()
        away_team_id = MockDataFactory.generate_id()
        home_team_name = MockDataFactory.generate_team_name()
        away_team_name = MockDataFactory.generate_team_name()
        home_team_club_id = MockDataFactory.generate_id()
        away_team_club_id = MockDataFactory.generate_id()

        home_officials = []
        away_officials = []

        # Generate home team officials
        for i, (role_id, role) in enumerate(
            [(1, "Tränare"), (2, "Assisterande tränare"), (3, "Lagledare")]
        ):
            # Generate a random Swedish personal number (YYYYMMDDXXXX)
            birth_year = random.randint(1960, 1990)  # Staff are typically older
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)  # Simplified to avoid invalid dates
            personal_number = (
                f"{birth_year}{birth_month:02d}{birth_day:02d}{random.randint(1000, 9999)}"
            )

            # Create official with the full structure from real data
            official = {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchlagledareJSON",
                "matchlagledareid": MockDataFactory.generate_id(),
                "matchid": match_id,
                "matchlagid": home_team_id,
                "personid": MockDataFactory.generate_id(),
                "fornamn": MockDataFactory.generate_name(True),
                "efternamn": MockDataFactory.generate_name(False),
                "personnr": personal_number,
                "matchlagnamn": home_team_name,
                "lagrollid": role_id,
                "lagrollnamn": role,
                "avvisadmatchminut": 0,
                "avvisadlindrig": False,
                "avvisadgrov": False,
                "varnad": False,
                "varnadmatchminut": 0,
                "ansvarig": i == 0,  # First official is responsible
                "foreningid": home_team_club_id,
                "ledareAntalAckumuleradeVarningar": 0,
                "ledareAvstangningBeskrivning": "",
            }

            home_officials.append(official)

        # Generate away team officials
        for i, (role_id, role) in enumerate(
            [(1, "Tränare"), (2, "Assisterande tränare"), (3, "Lagledare")]
        ):
            # Generate a random Swedish personal number (YYYYMMDDXXXX)
            birth_year = random.randint(1960, 1990)  # Staff are typically older
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)  # Simplified to avoid invalid dates
            personal_number = (
                f"{birth_year}{birth_month:02d}{birth_day:02d}{random.randint(1000, 9999)}"
            )

            # Create official with the full structure from real data
            official = {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchlagledareJSON",
                "matchlagledareid": MockDataFactory.generate_id(),
                "matchid": match_id,
                "matchlagid": away_team_id,
                "personid": MockDataFactory.generate_id(),
                "fornamn": MockDataFactory.generate_name(True),
                "efternamn": MockDataFactory.generate_name(False),
                "personnr": personal_number,
                "matchlagnamn": away_team_name,
                "lagrollid": role_id,
                "lagrollnamn": role,
                "avvisadmatchminut": 0,
                "avvisadlindrig": False,
                "avvisadgrov": False,
                "varnad": False,
                "varnadmatchminut": 0,
                "ansvarig": i == 0,  # First official is responsible
                "foreningid": away_team_club_id,
                "ledareAntalAckumuleradeVarningar": 0,
                "ledareAvstangningBeskrivning": "",
            }

            away_officials.append(official)

        return {
            "hemmalag": home_officials,
            "bortalag": away_officials,
        }

    @staticmethod
    def generate_match_events(
        match_id: Optional[int] = None, count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate sample match events based on real FOGIS API data structure."""
        if match_id is None:
            match_id = MockDataFactory.generate_id()

        events: List[Dict[str, Any]] = []
        home_score = 0
        away_score = 0

        # Generate home and away team IDs and names
        home_team_id = MockDataFactory.generate_id()
        away_team_id = MockDataFactory.generate_id()
        home_team_name = MockDataFactory.generate_team_name()
        away_team_name = MockDataFactory.generate_team_name()

        # Track related events (for substitutions)
        related_events: Dict[Union[int, str], Any] = {}
        # We'll store lists of event IDs under integer keys and sets under the "used" key

        # Generate a realistic sequence of events
        # We'll create a timeline of events that makes sense for a football match
        timeline = sorted(random.sample(range(1, 90), min(count, 20)))

        # Define event types based on real data
        event_types = [
            # (id, name, affects_score, requires_related_event)
            (6, "Spelmål", True, False),  # Regular goal
            (14, "Straffmål", True, False),  # Penalty goal
            (29, "Frisparksmål (Direkt i mål)", True, False),  # Free kick goal
            (20, "Varning", False, False),  # Yellow card
            (21, "Utvisning", False, False),  # Red card
            (16, "Byte ut", False, False),  # Substitution out
            (17, "Byte in", False, True),  # Substitution in (related to "Byte ut")
            (23, "Match slut", False, False),  # End of match
        ]

        # Add a match end event at 90 minutes
        if count > 1:
            timeline.append(90)

        # Generate events along the timeline
        for i, minute in enumerate(timeline):
            # For the last minute, always add a "Match slut" event
            if minute == 90 and i == len(timeline) - 1:
                event_type_id, event_type_name, affects_score, requires_related = (
                    23,
                    "Match slut",
                    False,
                    False,
                )
                team_id, team_name = 0, ""
                player_id, player_name = 0, " "
                jersey_number = -1
                participant_id = 0
            else:
                # Select a random event type (weighted towards more common events)
                weights = [10, 5, 2, 8, 3, 8, 8, 0]  # Higher weight = more likely
                event_type_index = random.choices(range(len(event_types)), weights=weights, k=1)[0]
                event_type_id, event_type_name, affects_score, requires_related = event_types[
                    event_type_index
                ]

                # For substitution in, we need a related "Byte ut" event
                if requires_related and event_type_id == 17:  # Byte in
                    # Skip if we don't have any "Byte ut" events to relate to
                    if 16 not in related_events:
                        continue

                    # Get the most recent "Byte ut" event that doesn't have a related "Byte in" yet
                    related_event_id = 0
                    for out_event_id in related_events.get(16, []):
                        if out_event_id not in related_events.get("used", set()):
                            related_event_id = out_event_id
                            # Mark this "Byte ut" as used
                            if "used" not in related_events:
                                related_events["used"] = set()
                            related_events["used"].add(out_event_id)
                            break
                    else:
                        # No unused "Byte ut" events found, skip this event
                        continue

                    # Use the same team as the related "Byte ut" event
                    for event in events:
                        if event["matchhandelseid"] == related_event_id:
                            team_id = event["matchlagid"]
                            team_name = event["matchlagnamn"]
                            break
                else:
                    # Determine team (home or away)
                    is_home_team = random.choice([True, False])
                    team_id = home_team_id if is_home_team else away_team_id
                    team_name = home_team_name if is_home_team else away_team_name
                    related_event_id = 0

                # Generate player details
                player_id = MockDataFactory.generate_id()
                player_name = MockDataFactory.generate_full_name()
                jersey_number = random.randint(1, 25)
                participant_id = MockDataFactory.generate_id()

            # Determine period based on minute
            period = 1 if minute <= 45 else 2

            # Update score for goal events
            if affects_score:
                is_home_team = team_id == home_team_id
                if is_home_team:
                    home_score += 1
                else:
                    away_score += 1

            # Create the event with the full structure from real data
            event = {
                "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchhandelseJSON",
                "matchhandelseid": MockDataFactory.generate_id(),
                "matchid": match_id,
                "matchdeltagareid": participant_id,
                "matchhandelsetypid": event_type_id,
                "matchhandelsetypnamn": event_type_name,
                "matchlagid": team_id,
                "matchlagnamn": team_name,
                "trojnummer": jersey_number,
                "spelareid": player_id,
                "spelarenamn": player_name,
                "matchminut": minute,
                "kommentar": "",
                "hemmamal": home_score if affects_score else 0,
                "bortamal": away_score if affects_score else 0,
                "period": period,
                "matchhandelsetypmedforstallningsandring": affects_score,
                "matchhandelsetypanvanderannonseradtid": False,
                "tidsangivelse": str(minute),
                "planpositionx": -1,
                "planpositiony": -1,
                "relateradTillMatchhandelseID": (related_event_id if requires_related else 0),
            }

            # Store event ID for potential related events
            if event_type_id == 16:  # Byte ut
                if 16 not in related_events:
                    related_events[16] = []
                related_events[16].append(event["matchhandelseid"])

            events.append(event)

        return events

    @staticmethod
    def generate_match_officials(match_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate sample match officials data."""
        if match_id is None:
            match_id = MockDataFactory.generate_id()

        # Generate home and away team IDs
        home_team_id = MockDataFactory.generate_id()
        away_team_id = MockDataFactory.generate_id()

        # Generate team names
        home_team_name = MockDataFactory.generate_team_name()
        away_team_name = MockDataFactory.generate_team_name()

        # Generate officials for both teams
        home_officials = []
        away_officials = []

        # Roles for officials
        roles = ["Tränare", "Assisterande tränare", "Lagledare", "Fysioterapeut", "Läkare"]

        # Generate 2-3 officials for each team
        for i in range(random.randint(2, 3)):
            # Home team official
            home_official = {
                "personid": MockDataFactory.generate_id(),
                "fornamn": MockDataFactory.generate_name(True),
                "efternamn": MockDataFactory.generate_name(False),
                "roll": roles[i % len(roles)],
                "matchlagid": home_team_id,
            }
            home_officials.append(home_official)

            # Away team official
            away_official = {
                "personid": MockDataFactory.generate_id(),
                "fornamn": MockDataFactory.generate_name(True),
                "efternamn": MockDataFactory.generate_name(False),
                "roll": roles[i % len(roles)],
                "matchlagid": away_team_id,
            }
            away_officials.append(away_official)

        # Combine all officials
        all_officials = home_officials + away_officials

        # Create the response structure
        response = {
            "hemmalag": home_team_name,
            "bortalag": away_team_name,
            "hemmalagid": home_team_id,
            "bortalagid": away_team_id,
            "matchid": match_id,
            "funktionarer": all_officials,
        }

        return response

    @staticmethod
    def generate_match_result_list(match_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate sample match result list data."""
        if match_id is None:
            match_id = MockDataFactory.generate_id()

        # Generate home and away team IDs
        home_team_id = MockDataFactory.generate_id()
        away_team_id = MockDataFactory.generate_id()

        # Generate team names
        home_team_name = MockDataFactory.generate_team_name()
        away_team_name = MockDataFactory.generate_team_name()

        # Generate result types
        result_types = [
            {"id": 1, "namn": "Ordinarie tid"},
            {"id": 2, "namn": "Efter förlängning"},
            {"id": 3, "namn": "Efter straffar"},
        ]

        # Generate random scores
        home_score = random.randint(0, 5)
        away_score = random.randint(0, 5)

        # Create result list
        results = [
            {
                "matchid": match_id,
                "matchresultattypid": 1,  # Ordinarie tid
                "matchlag1mal": home_score,
                "matchlag2mal": away_score,
                "wo": False,
                "ow": False,
                "ww": False,
            }
        ]

        # Create the response structure
        response = {
            "hemmalag": home_team_name,
            "bortalag": away_team_name,
            "hemmalagid": home_team_id,
            "bortalagid": away_team_id,
            "matchid": match_id,
            "matchresultattyper": result_types,
            "matchresultat": results,
        }

        return response

    @staticmethod
    def generate_match_result(match_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate sample match result based on real FOGIS API data structure."""
        if match_id is None:
            match_id = MockDataFactory.generate_id()

        home_goals = random.randint(0, 5)
        away_goals = random.randint(0, 5)
        halftime_home = min(home_goals, random.randint(0, 3))
        halftime_away = min(away_goals, random.randint(0, 3))

        # Create full-time result
        full_time_result = {
            "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchresultatJSON",
            "matchresultatid": MockDataFactory.generate_id(),
            "matchid": match_id,
            "matchresultattypid": 1,
            "matchresultattypnamn": "Slutresultat",
            "wo": False,
            "ow": False,
            "ww": False,
            "matchlag1mal": home_goals,
            "matchlag2mal": away_goals,
        }

        # Create half-time result
        half_time_result = {
            "__type": "Svenskfotboll.Fogis.Web.FogisMobilDomarKlient.MatchresultatJSON",
            "matchresultatid": MockDataFactory.generate_id(),
            "matchid": match_id,
            "matchresultattypid": 2,
            "matchresultattypnamn": "Resultat efter period 1",
            "wo": False,
            "ow": False,
            "ww": False,
            "matchlag1mal": halftime_home,
            "matchlag2mal": halftime_away,
        }

        return [full_time_result, half_time_result]

    @staticmethod
    def generate_team_players(team_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate sample team players data."""
        if team_id is None:
            team_id = MockDataFactory.generate_id()

        players = []
        # Generate 15-25 players
        for _ in range(random.randint(15, 25)):
            player_id = MockDataFactory.generate_id()
            first_name = MockDataFactory.generate_name(True)
            last_name = MockDataFactory.generate_name(False)
            jersey_number = random.randint(1, 99)
            position = random.choice(["Målvakt", "Försvarare", "Mittfältare", "Anfallare"])

            player = {
                "personid": player_id,
                "fornamn": first_name,
                "efternamn": last_name,
                "tshirt": jersey_number,
                "position": position,
                "matchlagid": team_id,
                "fodelsedatum": MockDataFactory.generate_date(False),
                "licensnummer": f"LIC{random.randint(100000, 999999)}",
                "spelarregistreringsstrang": "",
                "spelareAntalAckumuleradeVarningar": random.randint(0, 2),
                "spelareAvstangningBeskrivning": "",
            }

            players.append(player)

        return {"spelare": players}

    @staticmethod
    def generate_team_officials(team_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generate sample team officials data."""
        if team_id is None:
            team_id = MockDataFactory.generate_id()

        officials = []
        # Generate 2-5 officials
        roles = [
            "Tränare",
            "Assisterande tränare",
            "Lagledare",
            "Materialförvaltare",
            "Fysioterapeut",
        ]

        for i in range(random.randint(2, 5)):
            official_id = MockDataFactory.generate_id()
            first_name = MockDataFactory.generate_name(True)
            last_name = MockDataFactory.generate_name(False)
            role = roles[i % len(roles)]

            official = {
                "personid": official_id,
                "fornamn": first_name,
                "efternamn": last_name,
                "roll": role,
                "matchlagid": team_id,
                "fodelsedatum": MockDataFactory.generate_date(False),
                "licensnummer": f"LIC{random.randint(100000, 999999)}",
            }

            officials.append(official)

        return officials

    @staticmethod
    def get_sample_match_list_response() -> str:
        """Get a sample match list response as a JSON string."""
        match_list = MockDataFactory.generate_match_list()
        return json.dumps(match_list)

    @staticmethod
    def get_sample_match_details_response() -> str:
        """Get a sample match details response as a JSON string."""
        match_details = MockDataFactory.generate_match_details()
        return json.dumps({"d": json.dumps(match_details)})

    @staticmethod
    def get_sample_match_players_response() -> str:
        """Get a sample match players response as a JSON string."""
        match_players = MockDataFactory.generate_match_players()
        return json.dumps({"d": json.dumps(match_players)})

    @staticmethod
    def get_sample_match_officials_response() -> str:
        """Get a sample match officials response as a JSON string."""
        match_officials = MockDataFactory.generate_match_officials()
        return json.dumps({"d": json.dumps(match_officials)})

    @staticmethod
    def get_sample_match_events_response() -> str:
        """Get a sample match events response as a JSON string."""
        match_events = MockDataFactory.generate_match_events()
        return json.dumps({"d": match_events})

    @staticmethod
    def get_sample_match_result_response() -> str:
        """Get a sample match result response as a JSON string."""
        match_result = MockDataFactory.generate_match_result()
        return json.dumps({"d": match_result})


# Sample data for the mock server
SAMPLE_MATCH_LIST = MockDataFactory.generate_match_list()
SAMPLE_MATCH = MockDataFactory.generate_match_details()
SAMPLE_MATCH_PLAYERS = MockDataFactory.generate_match_players()
SAMPLE_MATCH_OFFICIALS = MockDataFactory.generate_match_officials()
SAMPLE_MATCH_EVENTS = MockDataFactory.generate_match_events()
SAMPLE_MATCH_RESULT = MockDataFactory.generate_match_result()


if __name__ == "__main__":
    # Print sample data
    print("Sample Match List:")
    print(json.dumps(SAMPLE_MATCH_LIST, indent=2))

    print("\nSample Match Details:")
    print(json.dumps(SAMPLE_MATCH, indent=2))

    print("\nSample Match Players:")
    print(json.dumps(SAMPLE_MATCH_PLAYERS, indent=2))

    print("\nSample Match Officials:")
    print(json.dumps(SAMPLE_MATCH_OFFICIALS, indent=2))

    print("\nSample Match Events:")
    print(json.dumps(SAMPLE_MATCH_EVENTS, indent=2))

    print("\nSample Match Result:")
    print(json.dumps(SAMPLE_MATCH_RESULT, indent=2))
