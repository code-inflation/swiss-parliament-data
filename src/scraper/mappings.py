"""Mapping functions for Swiss Parliament data."""


def get_canton_code(name: str | None) -> str | None:
    """Map canton name to two-letter code."""
    if name is None:
        return None

    canton_map = {
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

    return canton_map.get(name)


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
