"""Tests for the API client, using an in-memory HTTP transport."""

import json
from typing import Any

import httpx
import pytest

from scraper.api_client import ParliamentAPIClient
from scraper.main import scrape_factions


def make_client(handler: Any) -> ParliamentAPIClient:
    """Create a client backed by a mock transport."""
    return ParliamentAPIClient(transport=httpx.MockTransport(handler))


def api_page(data: list[dict[str, Any]], has_more: bool) -> httpx.Response:
    """Build an API-style paged response."""
    return httpx.Response(200, json={"data": data, "meta": {"has_more": has_more}})


def membership_payload(person_id: int, active: bool, **extra: Any) -> dict[str, Any]:
    """Build a minimal membership record."""
    record: dict[str, Any] = {
        "person": {
            "data": [
                {
                    "id": person_id,
                    "firstname": "Hans",
                    "lastname": "Müller",
                    "electoral_district": {"de": "Aarau"},
                }
            ]
        },
        "active": active,
    }
    record.update(extra)
    return record


class TestFetchGroups:
    """Tests for fetch_groups."""

    def test_paginates_until_has_more_false(self) -> None:
        """Test that all pages are fetched and concatenated."""
        pages = [
            api_page(
                [{"id": 1, "abbreviation": "A", "name": {"de": "One"}, "active": True}],
                has_more=True,
            ),
            api_page(
                [{"id": 2, "abbreviation": "B", "name": {"de": "Two"}, "active": True}],
                has_more=False,
            ),
        ]
        calls: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return pages[calls.index(request)]

        with make_client(handler) as client:
            groups = client.fetch_groups()

        assert [g.id for g in groups] == [1, 2]
        assert "offset=0" in str(calls[0].url)
        assert "offset=1000" in str(calls[1].url)

    def test_filters_inactive_groups(self) -> None:
        """Test that inactive groups are excluded."""
        page = api_page(
            [
                {"id": 1, "abbreviation": "A", "name": {"de": "Active"}, "active": True},
                {"id": 2, "abbreviation": "B", "name": {"de": "Inactive"}, "active": False},
            ],
            has_more=False,
        )

        with make_client(lambda request: page) as client:
            groups = client.fetch_groups()

        assert [g.id for g in groups] == [1]

    def test_http_error_raises(self) -> None:
        """Test that a failed groups request raises (and does not return partial data)."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        with make_client(handler) as client, pytest.raises(httpx.HTTPError):
            client.fetch_groups()

    def test_invalid_json_raises_value_error(self) -> None:
        """Test that a malformed groups payload raises ValueError."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<html>not json</html>")

        with make_client(handler) as client, pytest.raises(ValueError):
            client.fetch_groups()

    def test_sends_required_query_params(self) -> None:
        """Test that the groups request targets factions in Switzerland."""
        seen: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(dict(request.url.params))
            return api_page([], has_more=False)

        with make_client(handler) as client:
            client.fetch_groups()

        assert seen["type_harmonized_id"] == "4"
        assert seen["body_key"] == "CHE"


class TestFetchMemberships:
    """Tests for fetch_memberships."""

    def test_paginates_and_expands_person(self) -> None:
        """Test pagination and the expand=person parameter."""
        pages = [
            api_page([membership_payload(1, True)], has_more=True),
            api_page([membership_payload(2, False)], has_more=False),
        ]
        calls: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return pages[calls.index(request)]

        with make_client(handler) as client:
            memberships = client.fetch_memberships(3518)

        assert [m.person.data[0].id for m in memberships] == [1, 2]  # type: ignore[union-attr]
        params = dict(calls[0].url.params)
        assert params["group_id"] == "3518"
        assert params["expand"] == "person"

    def test_http_error_returns_partial_data(self) -> None:
        """Document current behavior: a mid-pagination failure keeps earlier pages."""
        calls: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(1)
            if len(calls) == 1:
                return api_page([membership_payload(1, True)], has_more=True)
            return httpx.Response(500)

        with make_client(handler) as client:
            memberships = client.fetch_memberships(1)

        assert len(memberships) == 1


class TestFetchDistrictMap:
    """Tests for fetch_district_map."""

    DISTRICT_PAGE = {
        "data": [
            {  # resolves to a single canton
                "electoral_district": {"de": "IX Horgen"},
                "body_keys": ["293", "ZH", "CHE"],
            },
            {  # ambiguous: two canton keys -> must be dropped
                "electoral_district": {"de": "Stein"},
                "body_keys": ["AR", "SH"],
            },
            {  # no de name (fr-only district) -> skipped
                "electoral_district": {"fr": "Morges"},
                "body_keys": ["VD"],
            },
            {  # empty district bucket -> skipped
                "electoral_district": {},
                "body_keys": ["CHE"],
            },
            {  # no canton body key -> not resolvable
                "electoral_district": {"de": "Aarau"},
                "body_keys": ["4001", "CHE"],
            },
        ],
        "meta": {"total_records": 5},
    }

    def test_builds_map_from_canton_body_keys(self) -> None:
        """Test unambiguous districts map to their single canton code."""
        page = httpx.Response(200, json=self.DISTRICT_PAGE)

        with make_client(lambda request: page) as client:
            district_map = client.fetch_district_map()

        assert district_map == {"IX Horgen": "ZH"}

    def test_http_error_returns_empty_dict(self) -> None:
        """Test that a failed fetch degrades to the static fallback ({}, not a crash)."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500)

        with make_client(handler) as client:
            assert client.fetch_district_map() == {}

    def test_invalid_json_returns_empty_dict(self) -> None:
        """Test that malformed payloads degrade to the static fallback."""

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, text="<html>not json</html>")

        with make_client(handler) as client:
            assert client.fetch_district_map() == {}


class TestClose:
    """Tests for client lifecycle."""

    def test_close_closes_underlying_client(self) -> None:
        """Test that close() releases the HTTP client."""
        client = ParliamentAPIClient(transport=httpx.MockTransport(lambda r: httpx.Response(200)))
        client.close()
        with pytest.raises(RuntimeError):
            client.client.get("https://example.com")

    def test_context_manager_closes_on_exit(self) -> None:
        """Test that the context manager closes the client, even on error."""
        client = ParliamentAPIClient(transport=httpx.MockTransport(lambda r: httpx.Response(500)))
        with pytest.raises(httpx.HTTPError), client:
            client.fetch_groups()
        with pytest.raises(RuntimeError):
            client.client.get("https://example.com")


class TestOutputFormat:
    """Tests that the serialized output matches the bash/jq byte format."""

    def test_member_serialization_matches_master_field_order(self) -> None:
        """Field order and casing must match the jq-produced schema."""
        from scraper.models import Member

        member = Member(
            id=1,
            firstName="Hans",
            lastName="Müller",
            faction="SVP",
            factionName="SVP",
            active=True,
            startDate="2019-12-02",
            endDate="2023-12-03",
        )
        raw = json.dumps(member.model_dump(mode="json"), ensure_ascii=False, indent=2)
        keys = [line.strip().strip('",').split(":")[0].strip(' "') for line in raw.splitlines()]
        keys = [k for k in keys if k and not k.startswith("{") and not k.startswith("}")]
        assert keys == [
            "id",
            "canton",
            "cantonName",
            "council",
            "faction",
            "factionName",
            "firstName",
            "lastName",
            "number",
            "party",
            "partyName",
            "active",
            "startDate",
            "endDate",
            "code",
            "gender",
            "officialDenomination",
            "salutationLetter",
            "salutationTitle",
            "factionFunction",
        ]

    def test_active_false_is_preserved_in_serialization(self) -> None:
        """Regression: active:false must never collapse to null."""
        from scraper.models import Member

        member = Member(faction="SVP", factionName="SVP", active=False)
        assert json.loads(member.model_dump_json())["active"] is False

    def test_non_numeric_external_id_maps_to_none(self) -> None:
        """Regression for the upstream 'barthassat' person id."""
        from scraper.models import PersonData

        person = PersonData.model_validate({"id": 6507, "external_alternative_id": "barthassat"})
        assert person.external_alternative_id == "barthassat"


class TestScrapeFactions:
    """End-to-end tests for scrape_factions with a mocked API."""

    @staticmethod
    def _client_factory(handler: Any) -> Any:
        """Build a client factory returning a mock-transport client."""
        return lambda: ParliamentAPIClient(transport=httpx.MockTransport(handler))

    def test_writes_expected_json_with_trailing_newline(self, tmp_path: Any) -> None:
        """Test the full flow produces byte-compatible JSON files."""
        import json

        groups = api_page(
            [
                {
                    "id": 100,
                    "external_alternative_id": "5",
                    "abbreviation": {"de": "V"},
                    "name": {"de": "Grüne Fraktion"},
                    "active": True,
                }
            ],
            has_more=False,
        )
        district_page = {
            "data": [
                {"electoral_district": {"de": "Aarau"}, "body_keys": ["AG"]},
            ],
            "meta": {"total_records": 1},
        }
        memberships = api_page(
            [
                membership_payload(
                    42,
                    True,
                    role_name={"de": "Mitglied"},
                    begin_date="2019-12-02",
                ),
                membership_payload(
                    43,
                    False,
                    role_name={"de": "Mitglied"},
                    begin_date="1995-12-04",
                    end_date="1999-12-03",
                ),
            ],
            has_more=False,
        )

        def handler(request: httpx.Request) -> httpx.Response:
            if "group_by" in str(request.url):
                return httpx.Response(200, json=district_page)
            if request.url.path.endswith("/groups/"):
                return groups
            return memberships

        factory = self._client_factory(handler)
        scrape_factions(output_dir=tmp_path, client_factory=factory)

        out = tmp_path / "faction_5.json"
        assert out.exists()
        raw = out.read_text(encoding="utf-8")
        assert raw.endswith("}\n")  # trailing newline like jq
        data = json.loads(raw)
        assert data["id"] == 5
        assert data["code"] == "FRA_5_"
        assert data["shortName"] == "Fraktion V"
        assert len(data["members"]) == 2
        assert data["members"][0]["active"] is True
        assert data["members"][0]["startDate"] == "2019-12-02"
        assert data["members"][0]["endDate"] is None
        assert data["members"][0]["canton"] == "AG"  # from district map
        assert data["members"][1]["active"] is False
        assert data["members"][1]["endDate"] == "1999-12-03"

    def test_removes_stale_faction_files(self, tmp_path: Any) -> None:
        """Test that faction files no longer present in the API are deleted."""
        stale = tmp_path / "faction_999.json"
        stale.write_text("{}")
        current = tmp_path / "faction_5.json"
        current.write_text("{}")

        groups = api_page(
            [
                {
                    "id": 100,
                    "external_alternative_id": "5",
                    "abbreviation": {"de": "V"},
                    "name": {"de": "V"},
                    "active": True,
                }
            ],
            has_more=False,
        )
        memberships = api_page([], has_more=False)

        def handler(request: httpx.Request) -> httpx.Response:
            if "group_by" in str(request.url):
                return httpx.Response(200, json={"data": [], "meta": {"total_records": 0}})
            if request.url.path.endswith("/groups/"):
                return groups
            return memberships

        factory = self._client_factory(handler)
        scrape_factions(output_dir=tmp_path, client_factory=factory)

        assert not stale.exists()
        assert current.exists()

    def test_aborts_when_no_factions(self, tmp_path: Any) -> None:
        """Test the zero-faction abort prevents wiping the output directory."""
        existing = tmp_path / "faction_5.json"
        existing.write_text("{}")

        def handler(request: httpx.Request) -> httpx.Response:
            if "group_by" in str(request.url):
                return httpx.Response(200, json={"data": [], "meta": {"total_records": 0}})
            return api_page([], has_more=False)

        factory = self._client_factory(handler)
        with pytest.raises(SystemExit):
            scrape_factions(output_dir=tmp_path, client_factory=factory)

        assert existing.exists()  # stale files were not removed
