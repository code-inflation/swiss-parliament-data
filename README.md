# Swiss Parliamentary Factions History

This repository tracks the history of Swiss parliamentary factions using the "Git scraping" technique, inspired by [Simon Willison's blog post](https://simonwillison.net/2020/Oct/9/git-scraping/) on the topic.

## Usage

The primary value of this repository lies in its Git history. By exploring the commits over time, you can track changes in faction memberships, details, and compositions.

You can use standard Git commands like `git log factions_details/` or `git diff <commit1> <commit2> -- factions_details/` to analyze the evolution of the data.

## Implementation and Data

The data represents the composition and details of various factions within the Swiss Parliament. It is scraped daily from the official parliamentary web service API.

A GitHub Actions workflow (`.github/workflows/scrape.yml`) runs a script (`scrape.sh`) daily to fetch the latest faction list and details. The script saves the data for each faction into a separate JSON file within the `factions_details/` directory (e.g., `faction_1.json`). Timestamps are removed from the data before saving to minimize commit noise. Changes are automatically committed, allowing the Git history to track the evolution of faction compositions over time.

