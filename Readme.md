# Engagements Fetcher Script

This Python script fetches bug bounty engagement data from Bugcrowd and extracts relevant scope targets from their changelogs.

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

You can install the required packages using pip:

```bash
pip install requests pyyaml
```

## Configuration

- In the config directory copy-paste `credentials.example.yaml` to `credentials.yaml`

- Add your credentials in the following format:

  ```yaml
  bc:
    cookie: "YOUR_COOKIE_HERE"
  ```

## Usage

- Run the script using Python:

  ```bash
  python main.py
  ```

  The script will create the following output files:
  targets.txt: Contains valid target URLs.
  wildcards.txt: Contains wildcard entries.
  invalid_urls.txt: Contains invalid URLs.
  domains.txt: Contains valid domains.

## Script Overview

### The script performs the following steps

- Loads credentials from the credentials.yaml file.
- Fetches engagements from the Bugcrowd API.
- Extracts changelog URLs for each engagement.
- Retrieves scope targets from the changelogs.
- Validates and categorizes the targets.
- Saves the categorized URLs to separate files.

## Customization

Feel free to play around or make any pull requests.

[Alejandro Sol](https://github.com/alejandro501)
