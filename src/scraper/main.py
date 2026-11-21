"""Main scraper logic for Swiss Parliament factions."""

import contextlib
import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path

from scraper.api_client import ParliamentAPIClient
from scraper.mappings import (
    extract_language_field,
    get_canton_code,
    get_council_code,
    get_faction_function,
)
from scraper.models import Faction, Member, MembershipData

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def process_memberships(
    memberships: list[MembershipData],
    faction_abbr: str,
    faction_name: str,
    district_map: dict[str, str] | None = None,
) -> list[Member]:
    """Process membership data into Member objects.

    Args:
        memberships: List of membership data from API
        faction_abbr: Faction abbreviation
        faction_name: Faction name
        district_map: Electoral district to canton code mapping from the API

    Returns:
        List of Member objects
    """
    members: list[Member] = []
    unknown_districts: set[str] = set()

    for membership in memberships:
        if not membership.person.data:
            continue

        person = membership.person.data[0]

        # Extract and convert person number; upstream occasionally contains
        # non-numeric identifiers (e.g. "barthassat" for person 6507)
        person_number = None
        if person.external_alternative_id:
            with contextlib.suppress(ValueError):
                person_number = int(person.external_alternative_id)

        # Extract language fields
        canton_name = extract_language_field(person.electoral_district)
        party_name = extract_language_field(person.party)
        party_harmonized = extract_language_field(person.party_harmonized)
        role_name = extract_language_field(membership.role_name)

        canton_code = get_canton_code(canton_name, district_map)
        if canton_name is not None and canton_code is None:
            unknown_districts.add(canton_name)

        member = Member(
            id=person.id,
            firstName=person.firstname,
            lastName=person.lastname,
            number=person_number,
            party=party_name,
            partyName=party_harmonized,
            faction=faction_abbr,
            factionName=faction_name,
            council=get_council_code(person.parliament_sector),
            canton=canton_code,
            cantonName=canton_name,
            gender=person.gender,
            active=membership.active,
            startDate=membership.begin_date,
            endDate=membership.end_date,
            factionFunction=get_faction_function(role_name),
            code=None,
            officialDenomination=None,
            salutationLetter=None,
            salutationTitle=None,
        )
        members.append(member)

    for district in sorted(unknown_districts):
        logger.warning(f"Unmapped electoral district, canton will be null: {district}")

    return members


def scrape_factions(
    output_dir: Path = Path("factions_details"),
    client_factory: Callable[[], ParliamentAPIClient] | None = None,
) -> None:
    """Scrape faction data and save to JSON files.

    Args:
        output_dir: Directory to save faction JSON files
        client_factory: Optional factory for the API client (mainly for testing)
    """
    output_dir.mkdir(exist_ok=True)

    with (client_factory or ParliamentAPIClient)() as client:
        # Fetch district → canton map first (needed by process_memberships)
        logger.info("Fetching electoral district → canton map...")
        district_map = client.fetch_district_map()
        logger.info(f"District map: {len(district_map)} resolvable districts")

        # Fetch all active groups
        logger.info("Fetching active parliamentary groups...")
        groups = client.fetch_groups()

        if not groups:
            logger.error("API returned 0 faction IDs. Aborting to prevent data loss.")
            sys.exit(1)

        # Extract faction IDs
        faction_ids = {
            g.external_alternative_id for g in groups if g.external_alternative_id is not None
        }
        logger.info(f"Faction IDs from API: {len(faction_ids)}")

        # Remove old faction files that are no longer in API
        for existing_file in output_dir.glob("faction_*.json"):
            existing_id = existing_file.stem.replace("faction_", "")
            if existing_id not in faction_ids:
                logger.info(f"Removing old faction file: {existing_file}")
                existing_file.unlink()

        # Process each group
        for group in groups:
            faction_id = group.external_alternative_id
            if not faction_id:
                logger.warning(f"Skipping group ID {group.id}: missing external_alternative_id")
                continue

            faction_abbr = extract_language_field(group.abbreviation) or ""
            faction_name = extract_language_field(group.name) or ""

            logger.info(f"Fetching memberships for faction ID: {faction_id} (group ID: {group.id})")

            # Fetch memberships
            memberships = client.fetch_memberships(group.id)
            members = process_memberships(memberships, faction_abbr, faction_name, district_map)

            # Create faction object
            faction = Faction(
                id=int(faction_id),
                abbreviation=faction_abbr,
                code=f"FRA_{faction_id}_",
                name=faction_name,
                shortName=f"Fraktion {faction_abbr}",
                members=members,
            )

            # Save to file
            output_file = output_dir / f"faction_{faction_id}.json"
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(
                    faction.model_dump(mode="json"),
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
                f.write("\n")
            logger.info(f"Saved faction {faction_id} to {output_file}")

    logger.info("Finished fetching all faction details.")


def main() -> None:
    """Main entry point."""
    try:
        scrape_factions()
    except Exception as e:
        logger.error(f"Scraping failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
