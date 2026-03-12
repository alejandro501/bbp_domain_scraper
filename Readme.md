# Bug Bounty Domain Scraper

Scrapes in-scope assets from Bugcrowd and HackerOne, then normalizes domain outputs.

## Project Structure

- `platforms/`: platform-specific scrapers (`bugcrowd.py`, `hackerone.py`, placeholders for `yeswehack.py`, `intigriti.py`)
- `utils/`: shared helpers (`io.py`, `post_digest.py`, markdown/report helpers)
- `config/`: runtime config/docs/constants
- `.docker/`: Docker build/run files
- `main.py`: orchestration CLI

## Credentials

Single source of truth: `.env`

Use `.env.example` as template and set:
- `BC_TOKEN`
- `H1_TOKEN`
- `YWH_TOKEN`

Legacy names still work for backward compatibility:
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

Run all programs (default mode):

```bash
python3 main.py --bc --h1 --mode all
```

Run only newly launched programs:

```bash
python3 main.py --h1 --mode new --interval last_week
python3 main.py --h1 --mode new --interval last_month
python3 main.py --h1 --mode new --days 15
```

## Output Structure

All outputs are stored in:

`data/<MM-DD-YYYY>/<interval>/`

Examples:
- `data/03-12-2026/all/`
- `data/03-12-2026/last_week/`
- `data/03-12-2026/15_days/`

Inside each interval folder:
- `targets.txt`
- `wildcards.txt`
- `domains.txt`
- `invalid_urls.txt` (if generated)
- `programs.md`
- `domain_trash/` backup files

## Markdown Report

`programs.md` format:

- `# programs`
- `## <date>`
- `### <program> (<platform>)`
- `#### wildcards`
- `#### domains`

Programs and dates are ordered newest to oldest.

## Docker

```bash
docker compose -f .docker/docker-compose.yml up --build
```

Run custom command:

```bash
docker compose -f .docker/docker-compose.yml run --rm bbp-scraper python main.py --h1 --mode new --days 15
```
