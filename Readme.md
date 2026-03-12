# Bug Bounty Domain Scraper

Scrapes in-scope assets from Bugcrowd and HackerOne, then normalizes domain outputs.

## Project Structure

- `platforms/`: platform-specific scrapers (`bugcrowd.py`, `hackerone.py`, placeholders for `yeswehack.py`, `intigriti.py`)
- `utils/`: shared helpers (`io.py`, `post_digest.py`)
- `config/`: runtime config docs/loader (`settings.py`)
- `.docker/`: Docker build/run files
- `main.py`: orchestration CLI

## Credentials

Single source of truth: `.env`

Use `.env.example` as template and set:
- `BC_COOKIE`
- `H1_COOKIE`
- `YWH_PAT`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Usage

Auth preflight:

```bash
python3 main.py --bc --h1 --check-auth
```

Run scrapers:

```bash
python3 main.py --bc
python3 main.py --h1
python3 main.py --bc --h1
```

Optional file flags:
- `--targets_file`
- `--wildcards_file`
- `--domains_file`
- `--invalid_urls_file`
- `--dotenv`

## Docker

```bash
docker compose -f .docker/docker-compose.yml up --build
```

Run custom command:

```bash
docker compose -f .docker/docker-compose.yml run --rm bbp-scraper python main.py --bc --h1
```
