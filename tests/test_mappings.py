"""Tests for mapping functions."""

from scraper.mappings import (
    extract_language_field,
    get_canton_code,
    get_council_code,
    get_faction_function,
)


class TestCantonCode:
    """Tests for canton code mapping."""

    def test_valid_canton_names(self) -> None:
        """Test mapping of valid canton names."""
        assert get_canton_code("Zürich") == "ZH"
        assert get_canton_code("Bern") == "BE"
        assert get_canton_code("Genf") == "GE"
        assert get_canton_code("Tessin") == "TI"
        assert get_canton_code("Aargau") == "AG"

    def test_appenzell_variations(self) -> None:
        """Test both forms of Appenzell canton names."""
        assert get_canton_code("Appenzell A.-Rh.") == "AR"
        assert get_canton_code("Appenzell Ausserrhoden") == "AR"
        assert get_canton_code("Appenzell I.-Rh.") == "AI"
        assert get_canton_code("Appenzell Innerrhoden") == "AI"

    def test_st_gallen_variations(self) -> None:
        """Test both forms of St. Gallen."""
        assert get_canton_code("St. Gallen") == "SG"
        assert get_canton_code("Sankt Gallen") == "SG"

    def test_invalid_canton_name(self) -> None:
        """Test that invalid canton names return None."""
        assert get_canton_code("InvalidCanton") is None
        assert get_canton_code("") is None

    def test_none_input(self) -> None:
        """Test that None input returns None."""
        assert get_canton_code(None) is None


class TestCouncilCode:
    """Tests for council code mapping."""

    def test_valid_sectors(self) -> None:
        """Test mapping of valid parliament sectors."""
        assert get_council_code("NR") == "N"
        assert get_council_code("SR") == "S"

    def test_invalid_sector(self) -> None:
        """Test that invalid sectors return None."""
        assert get_council_code("XX") is None
        assert get_council_code("") is None

    def test_none_input(self) -> None:
        """Test that None input returns None."""
        assert get_council_code(None) is None


class TestFactionFunction:
    """Tests for faction function mapping."""

    def test_valid_roles(self) -> None:
        """Test mapping of valid role names."""
        assert get_faction_function("Mitglied") == 1
        assert get_faction_function("Präsident/in") == 2
        assert get_faction_function("Vizepräsident/in") == 11

    def test_invalid_role(self) -> None:
        """Test that invalid roles return None."""
        assert get_faction_function("InvalidRole") is None
        assert get_faction_function("") is None

    def test_none_input(self) -> None:
        """Test that None input returns None."""
        assert get_faction_function(None) is None


class TestExtractLanguageField:
    """Tests for language field extraction."""

    def test_dict_with_german(self) -> None:
        """Test extraction from dict with German field."""
        value = {"de": "German text", "fr": "French text"}
        assert extract_language_field(value) == "German text"

    def test_dict_without_german(self) -> None:
        """Test extraction from dict without German field."""
        value = {"fr": "French text"}
        assert extract_language_field(value) is None

    def test_string_input(self) -> None:
        """Test that string input is returned as-is."""
        assert extract_language_field("plain string") == "plain string"

    def test_none_input(self) -> None:
        """Test that None input returns None."""
        assert extract_language_field(None) is None

    def test_empty_dict(self) -> None:
        """Test extraction from empty dict."""
        assert extract_language_field({}) is None
