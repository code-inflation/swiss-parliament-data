"""Data models for Swiss Parliament scraper."""

from pydantic import BaseModel


class MetaResponse(BaseModel):
    """API pagination metadata."""

    has_more: bool


class GroupData(BaseModel):
    """Parliamentary group data from API."""

    id: int
    external_alternative_id: str | None = None
    abbreviation: dict[str, str] | str
    name: dict[str, str] | str
    active: bool


class GroupResponse(BaseModel):
    """API response for groups endpoint."""

    data: list[GroupData]
    meta: MetaResponse


class PersonData(BaseModel):
    """Person data embedded in membership response."""

    id: int | None = None
    firstname: str | None = None
    lastname: str | None = None
    external_alternative_id: str | None = None
    electoral_district: dict[str, str] | str | None = None
    parliament_sector: str | None = None
    party: dict[str, str] | str | None = None
    party_harmonized: dict[str, str] | str | None = None
    gender: str | None = None


class PersonWrapper(BaseModel):
    """Wrapper for person data in membership response."""

    data: list[PersonData]


class MembershipData(BaseModel):
    """Membership data from API."""

    person: PersonWrapper
    active: bool | None = None
    role_name: dict[str, str] | str | None = None


class MembershipResponse(BaseModel):
    """API response for memberships endpoint."""

    data: list[MembershipData]
    meta: MetaResponse


class Member(BaseModel):
    """Member information in faction output."""

    id: int | None = None
    firstName: str | None = None
    lastName: str | None = None
    number: int | None = None
    party: str | None = None
    partyName: str | None = None
    faction: str
    factionName: str
    council: str | None = None
    canton: str | None = None
    cantonName: str | None = None
    gender: str | None = None
    active: bool | None = None
    factionFunction: int | None = None
    code: None = None
    officialDenomination: None = None
    salutationLetter: None = None
    salutationTitle: None = None


class Faction(BaseModel):
    """Faction data output."""

    id: int
    abbreviation: str
    code: str
    name: str
    shortName: str
    members: list[Member]
