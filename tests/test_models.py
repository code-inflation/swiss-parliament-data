"""Tests for data models."""

from scraper.models import (
    DistrictMapEntry,
    DistrictMapResponse,
    Faction,
    GroupData,
    GroupResponse,
    Member,
    MembershipData,
    MetaResponse,
    PersonData,
)


class TestMetaResponse:
    """Tests for MetaResponse model."""

    def test_valid_meta(self) -> None:
        """Test valid meta response."""
        meta = MetaResponse(has_more=True)
        assert meta.has_more is True

    def test_meta_dict(self) -> None:
        """Test creation from dict."""
        meta = MetaResponse.model_validate({"has_more": False})
        assert meta.has_more is False


class TestGroupData:
    """Tests for GroupData model."""

    def test_valid_group_with_dict_fields(self) -> None:
        """Test group with multilingual dict fields."""
        group = GroupData(
            id=1,
            external_alternative_id="123",
            abbreviation={"de": "SVP", "fr": "UDC"},
            name={"de": "Schweizerische Volkspartei"},
            active=True,
        )
        assert group.id == 1
        assert group.external_alternative_id == "123"
        assert isinstance(group.abbreviation, dict)

    def test_valid_group_with_string_fields(self) -> None:
        """Test group with string fields."""
        group = GroupData(
            id=1,
            external_alternative_id="123",
            abbreviation="SVP",
            name="Schweizerische Volkspartei",
            active=True,
        )
        assert group.abbreviation == "SVP"
        assert group.name == "Schweizerische Volkspartei"

    def test_optional_external_id(self) -> None:
        """Test that external_alternative_id is optional."""
        group = GroupData(
            id=1,
            abbreviation="TEST",
            name="Test Group",
            active=False,
        )
        assert group.external_alternative_id is None


class TestGroupResponse:
    """Tests for GroupResponse model."""

    def test_valid_response(self) -> None:
        """Test valid API response."""
        response_data = {
            "data": [
                {
                    "id": 1,
                    "external_alternative_id": "123",
                    "abbreviation": "SVP",
                    "name": "Schweizerische Volkspartei",
                    "active": True,
                }
            ],
            "meta": {"has_more": False},
        }
        response = GroupResponse.model_validate(response_data)
        assert len(response.data) == 1
        assert response.meta.has_more is False


class TestPersonData:
    """Tests for PersonData model."""

    def test_all_fields_optional(self) -> None:
        """Test that all fields are optional."""
        person = PersonData()
        assert person.id is None
        assert person.firstname is None
        assert person.lastname is None

    def test_with_all_fields(self) -> None:
        """Test person with all fields."""
        person = PersonData(
            id=1,
            firstname="Hans",
            lastname="Müller",
            external_alternative_id="456",
            electoral_district={"de": "Zürich"},
            parliament_sector="NR",
            party="SVP",
            party_harmonized={"de": "SVP"},
            gender="m",
        )
        assert person.firstname == "Hans"
        assert person.parliament_sector == "NR"


class TestMember:
    """Tests for Member model."""

    def test_required_fields_only(self) -> None:
        """Test member with only required fields."""
        member = Member(
            faction="SVP",
            factionName="Schweizerische Volkspartei",
        )
        assert member.faction == "SVP"
        assert member.code is None
        assert member.officialDenomination is None

    def test_with_all_fields(self) -> None:
        """Test member with all fields."""
        member = Member(
            id=1,
            firstName="Hans",
            lastName="Müller",
            number=456,
            party="SVP",
            partyName="SVP",
            faction="SVP",
            factionName="Schweizerische Volkspartei",
            council="N",
            canton="ZH",
            cantonName="Zürich",
            gender="m",
            active=True,
            factionFunction=1,
            code=None,
            officialDenomination=None,
            salutationLetter=None,
            salutationTitle=None,
        )
        assert member.firstName == "Hans"
        assert member.canton == "ZH"
        assert member.factionFunction == 1


class TestFaction:
    """Tests for Faction model."""

    def test_valid_faction(self) -> None:
        """Test valid faction."""
        faction = Faction(
            id=1,
            abbreviation="SVP",
            code="FRA_1_",
            name="Schweizerische Volkspartei",
            shortName="Fraktion SVP",
            members=[],
        )
        assert faction.id == 1
        assert faction.code == "FRA_1_"
        assert len(faction.members) == 0

    def test_faction_with_members(self) -> None:
        """Test faction with members."""
        member = Member(faction="SVP", factionName="Test")
        faction = Faction(
            id=1,
            abbreviation="SVP",
            code="FRA_1_",
            name="Test",
            shortName="Fraktion SVP",
            members=[member],
        )
        assert len(faction.members) == 1
        assert faction.members[0].faction == "SVP"


class TestMembershipDates:
    """Tests for membership begin/end date fields."""

    def test_dates_parsed(self) -> None:
        """Test begin_date and end_date are captured from API payload."""
        membership = MembershipData.model_validate(
            {
                "person": {"data": []},
                "active": False,
                "begin_date": "2019-12-02",
                "end_date": "2023-12-03",
            }
        )
        assert membership.begin_date == "2019-12-02"
        assert membership.end_date == "2023-12-03"

    def test_missing_dates_optional(self) -> None:
        """Test begin_date/end_date default to None when absent."""
        membership = MembershipData.model_validate({"person": {"data": []}})
        assert membership.begin_date is None
        assert membership.end_date is None


class TestDistrictMapModels:
    """Tests for the group_by electoral_districts response models."""

    def test_entry_with_district_and_bodies(self) -> None:
        """Test a district bucket with de name and body keys."""
        entry = DistrictMapEntry.model_validate(
            {
                "electoral_district": {"de": "IX Horgen"},
                "body_keys": ["293", "ZH", "CHE"],
            }
        )
        assert entry.electoral_district is not None
        assert entry.electoral_district["de"] == "IX Horgen"
        assert "ZH" in entry.body_keys

    def test_entry_without_de_name(self) -> None:
        """Test a bucket missing the de name (fr-only districts)."""
        entry = DistrictMapEntry.model_validate(
            {"electoral_district": {"fr": "Morges"}, "body_keys": ["CHE"]}
        )
        assert entry.electoral_district is not None
        assert "de" not in entry.electoral_district

    def test_entry_with_empty_district(self) -> None:
        """Test the null-district bucket (empty object)."""
        entry = DistrictMapEntry.model_validate({"electoral_district": {}, "body_keys": []})
        assert entry.electoral_district == {}

    def test_response_meta_without_has_more(self) -> None:
        """The group_by endpoint's meta has no has_more; parsing must not require it."""
        response = DistrictMapResponse.model_validate(
            {
                "data": [{"electoral_district": {"de": "Aarau"}, "body_keys": ["AG"]}],
                "meta": {"total_records": 521},
            }
        )
        assert len(response.data) == 1
        assert response.meta is not None
        assert response.meta.total_records == 521

    def test_response_without_meta(self) -> None:
        """Test that a missing meta block is tolerated."""
        response = DistrictMapResponse.model_validate(
            {"data": [{"electoral_district": {"de": "Aarau"}, "body_keys": ["AG"]}]}
        )
        assert response.meta is None
