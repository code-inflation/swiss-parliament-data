"""Tests for main scraper logic."""

from scraper.main import process_memberships
from scraper.models import MembershipData, PersonData, PersonWrapper


class TestProcessMemberships:
    """Tests for process_memberships function."""

    def test_empty_memberships(self) -> None:
        """Test processing empty membership list."""
        members = process_memberships([], "SVP", "Schweizerische Volkspartei")
        assert members == []

    def test_membership_without_person_data(self) -> None:
        """Test membership with no person data."""
        membership = MembershipData(
            person=PersonWrapper(data=[]),
            active=True,
        )
        members = process_memberships([membership], "SVP", "Test")
        assert members == []

    def test_single_membership(self) -> None:
        """Test processing single membership."""
        person = PersonData(
            id=1,
            firstname="Hans",
            lastname="Müller",
            external_alternative_id="456",
            electoral_district="Zürich",
            parliament_sector="NR",
            party="SVP",
            party_harmonized="SVP",
            gender="m",
        )
        membership = MembershipData(
            person=PersonWrapper(data=[person]),
            active=True,
            role_name="Mitglied",
        )

        members = process_memberships([membership], "SVP", "Schweizerische Volkspartei")

        assert len(members) == 1
        member = members[0]
        assert member.id == 1
        assert member.firstName == "Hans"
        assert member.lastName == "Müller"
        assert member.number == 456
        assert member.faction == "SVP"
        assert member.factionName == "Schweizerische Volkspartei"
        assert member.canton == "ZH"
        assert member.council == "N"
        assert member.factionFunction == 1

    def test_multilingual_fields(self) -> None:
        """Test processing membership with multilingual fields."""
        person = PersonData(
            id=1,
            electoral_district={"de": "Genf", "fr": "Genève"},
            party={"de": "SP", "fr": "PS"},
            party_harmonized={"de": "SP"},
        )
        membership = MembershipData(
            person=PersonWrapper(data=[person]),
            active=True,
            role_name={"de": "Präsident/in", "fr": "Président/e"},
        )

        members = process_memberships([membership], "SP", "Sozialdemokratische Partei")

        assert len(members) == 1
        member = members[0]
        assert member.cantonName == "Genf"
        assert member.canton == "GE"
        assert member.party == "SP"
        assert member.factionFunction == 2

    def test_invalid_person_number(self) -> None:
        """Test handling of invalid person number."""
        person = PersonData(
            id=1,
            external_alternative_id="invalid",
        )
        membership = MembershipData(
            person=PersonWrapper(data=[person]),
            active=True,
        )

        members = process_memberships([membership], "TEST", "Test")

        assert len(members) == 1
        assert members[0].number is None

    def test_multiple_memberships(self) -> None:
        """Test processing multiple memberships."""
        person1 = PersonData(id=1, firstname="Hans", lastname="Müller")
        person2 = PersonData(id=2, firstname="Maria", lastname="Schmidt")

        membership1 = MembershipData(
            person=PersonWrapper(data=[person1]),
            active=True,
        )
        membership2 = MembershipData(
            person=PersonWrapper(data=[person2]),
            active=False,
        )

        members = process_memberships([membership1, membership2], "SVP", "Test")

        assert len(members) == 2
        assert members[0].firstName == "Hans"
        assert members[1].firstName == "Maria"
        assert members[0].active is True
        assert members[1].active is False
