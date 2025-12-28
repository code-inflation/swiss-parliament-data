"""Tests for data models."""

from scraper.models import (
    Faction,
    GroupData,
    GroupResponse,
    Member,
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
