"""Mapping functions for Swiss Parliament data."""

# Static fallback for entries the API-derived district map cannot resolve:
# the 26 canton names themselves, plus "La Vallée" (a Vaud constituency that
# the API only exposes under its French name with no canton body key).
CANTON_NAME_TO_CODE = {
    "Aargau": "AG",
    "Appenzell A.-Rh.": "AR",
    "Appenzell Ausserrhoden": "AR",
    "Appenzell I.-Rh.": "AI",
    "Appenzell Innerrhoden": "AI",
    "Basel-Landschaft": "BL",
    "Basel-Stadt": "BS",
    "Bern": "BE",
    "Freiburg": "FR",
    "Genf": "GE",
    "Glarus": "GL",
    "Graubünden": "GR",
    "Jura": "JU",
    "La Vallée": "VD",
    "Luzern": "LU",
    "Neuenburg": "NE",
    "Nidwalden": "NW",
    "Obwalden": "OW",
    "Schaffhausen": "SH",
    "Schwyz": "SZ",
    "Solothurn": "SO",
    "St. Gallen": "SG",
    "Sankt Gallen": "SG",
    "Tessin": "TI",
    "Thurgau": "TG",
    "Uri": "UR",
    "Waadt": "VD",
    "Wallis": "VS",
    "Zug": "ZG",
    "Zürich": "ZH",
}


def get_canton_code(name: str | None, district_map: dict[str, str] | None = None) -> str | None:
    """Map a district or canton name to its two-letter canton code.

    The API's electoral_district field usually contains a constituency name
    (e.g. "Aarau", "Kleinbasel", "IX Horgen"), so the dynamic district map
    derived from the API is consulted first; well-known canton names are
    handled by the static fallback map.

    Args:
        name: Electoral district or canton name
        district_map: District-to-canton mapping fetched from the API
            (may be empty or None if the fetch failed)

    Returns:
        Two-letter canton code, or None if unresolvable
    """
    if name is None:
        return None

    if district_map:
        code = district_map.get(name)
        if code is not None:
            return code

    return CANTON_NAME_TO_CODE.get(name)


def get_council_code(sector: str | None) -> str | None:
    """Map parliament sector to council code."""
    if sector is None:
        return None

    council_map = {
        "NR": "N",  # National Council
        "SR": "S",  # States Council
    }

    return council_map.get(sector)


def get_faction_function(role: str | None) -> int | None:
    """Map role name to faction function code."""
    if role is None:
        return None

    function_map = {
        "Mitglied": 1,  # Member
        "Präsident/in": 2,  # President
        "Vizepräsident/in": 11,  # Vice President
    }

    return function_map.get(role)


def extract_language_field(value: dict[str, str] | str | None) -> str | None:
    """Extract German language field from multilingual object or return string as-is."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get("de")
    return value
