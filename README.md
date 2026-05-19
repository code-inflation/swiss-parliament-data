# Swiss Parliamentary Factions History

This repository tracks the history of Swiss parliamentary factions using the "Git scraping" technique, inspired by [Simon Willison's blog post](https://simonwillison.net/2020/Oct/9/git-scraping/) on the topic.

## Usage

The primary value of this repository lies in its Git history. By exploring the commits over time, you can track changes in faction memberships, details, and compositions.

You can use standard Git commands like `git log factions_details/` or `git diff <commit1> <commit2> -- factions_details/` to analyze the evolution of the data.

## Implementation and Data

The data represents the composition and details of various factions within the Swiss Parliament. It is scraped daily from the [OpenParlData API](https://api.openparldata.ch).

A GitHub Actions workflow (`.github/workflows/scrape.yml`) runs a Python scraper daily to fetch the latest faction list and details. The scraper saves the data for each faction into a separate JSON file within the `factions_details/` directory (e.g., `faction_1.json`). Changes are automatically committed, allowing the Git history to track the evolution of faction compositions over time.

## Development

This project uses modern Python tooling:

- **[UV](https://github.com/astral-sh/uv)** for fast dependency management
- **[Ruff](https://github.com/astral-sh/ruff)** for linting and formatting
- **[mypy](https://mypy-lang.org/)** for static type checking
- **[pytest](https://pytest.org/)** for testing

### Setup

Install dependencies with UV:

```bash
uv sync
```

### Running the Scraper

Run the scraper locally:

```bash
uv run python -m scraper.main
```

### Development Commands

Run linting:

```bash
uv run ruff check .
uv run ruff format .
```

Run type checking:

```bash
uv run mypy --package scraper
```

Run tests:

```bash
uv run pytest
```

### Project Structure

```
.
├── src/
│   └── scraper/
│       ├── __init__.py
│       ├── main.py          # Main scraping logic
│       ├── api_client.py    # API client for OpenParlData
│       ├── models.py        # Pydantic data models
│       └── mappings.py      # Mapping functions (canton codes, etc.)
├── tests/                   # Test suite
├── factions_details/        # Output directory for faction JSON files
└── pyproject.toml          # Project configuration
```

