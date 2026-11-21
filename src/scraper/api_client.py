"""API client for Swiss Parliament data."""

import logging
from typing import Any

import httpx

from scraper.models import (
    DistrictMapResponse,
    GroupData,
    GroupResponse,
    MembershipData,
    MembershipResponse,
)  # noqa: E501

logger = logging.getLogger(__name__)

# Official two-letter canton codes, used to identify canton bodies in the
# district map fetched from /persons/group_by/electoral_districts.
CANTON_CODES = frozenset(
    [
        "AG",
        "AI",
        "AR",
        "BE",
        "BL",
        "BS",
        "FR",
        "GE",
        "GL",
        "GR",
        "JU",
        "LU",
        "NE",
        "NW",
        "OW",
        "SG",
        "SH",
        "SO",
        "SZ",
        "TG",
        "TI",
        "UR",
        "VD",
        "VS",
        "ZG",
        "ZH",
    ]
)


class ParliamentAPIClient:
    """Client for interacting with the Swiss Parliament API."""

    BASE_URL = "https://api.openparldata.ch/v1"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/58.0.3029.110 Safari/537.36"
    )
    LIMIT = 1000

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """Initialize API client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            transport: Optional custom HTTP transport (mainly for testing)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.Client(
            timeout=timeout,
            headers={"User-Agent": self.USER_AGENT},
            transport=transport or httpx.HTTPTransport(retries=max_retries),
        )

    def __enter__(self) -> "ParliamentAPIClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.client.close()

    def fetch_groups(self) -> list[GroupData]:
        """Fetch all active parliamentary groups.

        Returns:
            List of active group data

        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If API response is invalid
        """
        groups: list[GroupData] = []
        offset = 0

        while True:
            params: dict[str, int | str] = {
                "type_harmonized_id": 4,
                "body_key": "CHE",
                "offset": offset,
                "limit": self.LIMIT,
            }

            response = self.client.get(f"{self.BASE_URL}/groups/", params=params)
            response.raise_for_status()

            try:
                group_response = GroupResponse.model_validate(response.json())
            except Exception as e:
                logger.error(f"Failed to parse groups response: {e}")
                raise ValueError(f"Invalid JSON response from groups API: {e}") from e

            # Filter for active groups
            active_groups = [g for g in group_response.data if g.active]
            groups.extend(active_groups)

            if not group_response.meta.has_more:
                break

            offset += self.LIMIT

        return groups

    def fetch_memberships(self, group_id: int) -> list[MembershipData]:
        """Fetch all memberships for a specific group (active and historical).

        Args:
            group_id: The group ID to fetch memberships for

        Returns:
            List of membership data

        Raises:
            httpx.HTTPError: If API request fails
        """
        memberships: list[MembershipData] = []
        offset = 0

        while True:
            params: dict[str, int | str] = {
                "group_id": group_id,
                "expand": "person",
                "offset": offset,
                "limit": self.LIMIT,
            }

            try:
                response = self.client.get(f"{self.BASE_URL}/memberships/", params=params)
                response.raise_for_status()

                membership_response = MembershipResponse.model_validate(response.json())
                memberships.extend(membership_response.data)

                if not membership_response.meta.has_more:
                    break

                offset += self.LIMIT

            except httpx.HTTPError as e:
                logger.warning(f"Failed to fetch memberships for group {group_id}: {e}")
                # Continue with what we have rather than failing completely
                break

        return memberships

    def fetch_district_map(self) -> dict[str, str]:
        """Fetch a mapping from electoral district name to canton code.

        The API's electoral_district field often contains constituency names
        (e.g. "Aarau", "Kleinbasel", "IX Horgen") rather than canton names, so
        the canton cannot be derived from the person record alone. This endpoint
        groups all persons by district and exposes the associated body keys,
        among which the two-letter canton code can be identified.

        Returns:
            Mapping of district name to canton code. Entries where the canton
            is ambiguous (multiple canton body keys) are omitted. Returns an
            empty dict if the fetch fails (static fallback still applies).
        """
        cantons_by_district: dict[str, set[str]] = {}

        try:
            # The group_by endpoint ignores limit/offset and returns all
            # buckets in one page, so a single request suffices.
            response = self.client.get(
                f"{self.BASE_URL}/persons/group_by/electoral_districts",
                params={"limit": self.LIMIT},
            )
            response.raise_for_status()
            district_response = DistrictMapResponse.model_validate(response.json())
        except (httpx.HTTPError, ValueError) as e:
            logger.warning(
                "Could not fetch electoral district map, "
                f"falling back to static canton names only: {e}"
            )
            return {}

        for entry in district_response.data:
            name = (entry.electoral_district or {}).get("de")
            if not name:
                continue
            found = cantons_by_district.setdefault(name, set())
            found.update(k for k in entry.body_keys if k in CANTON_CODES)

        # Drop ambiguous districts (e.g. "Stein" exists in AR and SH) rather
        # than guessing, and represent resolvable ones as a single code.
        district_map: dict[str, str] = {}
        for name, cantons in sorted(cantons_by_district.items()):
            if len(cantons) == 1:
                district_map[name] = next(iter(cantons))
        return district_map

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()
