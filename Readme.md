# Bug Bounty Domain Scraper

This tool fetches bug bounty program scope data from Bugcrowd and HackerOne and extracts all scope targets.

## Fork ideas
- Feel free to integrate the flow into other popular or not so popular bug bounty platforms too.

## Features

- Fetches engagements based on the specified criteria.
- Extracts valid target URLs and saves them to a file.
- Categorizes URLs into valid, invalid, and wildcard entries.
- Supports configuration via a credentials file.

## Prerequisites

Before running the script, ensure you have the following installed:

- Python 3.x
- Required Python packages:
  - `requests`
  - `PyYAML`
  - `beautifulsoup4`

You can install the required packages using pip:

```bash
pip install -r requirements.txt
```

## Configuration

- In the config directory copy-paste `credentials.example.yaml` to `credentials.yaml`

- Add your credentials in the following format:

```json
{
  "credentials": {
    "bc": {
      "cookie": "full_cookie"
    },
    "h1": {
      "cookie": "full_cookie"
    }
  },
  "webhooks": {
      "discord": {
          "general_vps_output": "https://discordapp.com/api/webhooks/channel/id"
      }
  }
}
```

## Usage

  ```bash
usage: main.py [-h] [--bc] [--ywh] [--h1] --config CONFIG [--targets_file TARGETS_FILE] [--wildcards_file WILDCARDS_FILE] [--domains_file DOMAINS_FILE] [--invalid_urls_file INVALID_URLS_FILE]

Run scripts for programs.

options:
  -h, --help            show this help message and exit
  --bc                  Run BC script
  --ywh                 Run YWH script
  --h1                  Run H1 script
  --config CONFIG, -C CONFIG
                        JSON config file
  --targets_file TARGETS_FILE
                        Output file for targets
  --wildcards_file WILDCARDS_FILE
                        Wildcards file
  --domains_file DOMAINS_FILE
                        Output file for domains
  --invalid_urls_file INVALID_URLS_FILE
                        Output file for invalid URLs
  ```

  The script will create the following output files:
  targets.txt:      valid target URLs.
  wildcards.txt:    wildcard entries.
  invalid_urls.txt: invalid URLs.
  domains.txt:      valid domains.

## Scripts Overview

### Bugcrowd

- Loads credentials from config.json.
- Fetches engagement data from the Bugcrowd website.
- Generates URLs for each engagement.
- Extracts the changelog URL for each engagement.
- Fetches the changelog data and extracts scope targets.
- Validates whether each target is a valid URL.
- Categorizes the targets into valid URLs, invalid URLs, and wildcards.
- Saves the categorized URLs to separate files: domains.txt, invalid_urls.txt, and wildcards.txt.

### HackerOne

- Loads credentials from config.json.
- Makes requests to the HackerOne API using GraphQL to fetch opportunities and identifiers.
- Fetches opportunities from HackerOne API, with sorting options like launched_at or minimum_bounty_table_value.
- Fetches identifiers (wildcards and domains) for handles listed in targets.txt.
- Categorizes the identifiers into wildcards and domains based on the display name.
- Saves wildcards and domains into wildcards.txt and domains.txt, respectively.
- Removes duplicates from the result files (wildcards.txt, domains.txt).
- Optionally handles different sorting strategies for fetching opportunities, such as ascending/descending order of launch date or bounty amount.

## Customization

Feel free to play around or make any pull requests.

[Alejandro Sol](https://github.com/alejandro501)
