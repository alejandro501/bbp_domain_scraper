import argparse
import os
from datetime import datetime, timedelta, timezone

from config.constants import (
    DATA_DIR,
    DOMAINS_BASENAME,
    INVALID_URLS_BASENAME,
    PROGRAMS_MD_BASENAME,
    TARGETS_BASENAME,
    WILDCARDS_BASENAME,
)
from config.settings import load_dotenv, load_runtime_config
from platforms import bugcrowd, hackerone
from utils import post_digest
from utils.models import QueryOptions
from utils.report import write_programs_markdown


def ensure_file_exists(file_path):
    """Ensure that a file exists; if not, create it."""
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    if not os.path.exists(file_path):
        print(f"Creating empty file: {file_path}")
        with open(file_path, "w", encoding="utf-8"):
            pass


def run_post_processing(wildcards_file, domains_file, invalid_urls_file):
    """Run post-processing only when source files exist."""
    if os.path.exists(wildcards_file):
        post_digest.clean_wildcards(wildcards_file, domains_file)

    if os.path.exists(invalid_urls_file):
        post_digest.clean_invalid_urls(invalid_urls_file, domains_file)

    if os.path.exists(domains_file):
        post_digest.add_https_to_domains(domains_file)
        post_digest.remove_duplicate_domains(domains_file)


def build_query_options(mode: str, interval: str | None, days: int | None) -> QueryOptions:
    if mode == "all":
        return QueryOptions(mode="all", cutoff=None, interval_label="all")

    if days is not None:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        return QueryOptions(mode="new", cutoff=cutoff, interval_label=f"{days}_days")

    if interval == "last_month":
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
        return QueryOptions(mode="new", cutoff=cutoff, interval_label="last_month")

    # default new window
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
    return QueryOptions(mode="new", cutoff=cutoff, interval_label="last_week")


def build_output_paths(query_options: QueryOptions) -> dict[str, str]:
    timestamp = datetime.now().strftime("%m-%d-%Y")
    base_dir = os.path.join(DATA_DIR, timestamp, query_options.interval_label)

    return {
        "base_dir": base_dir,
        "targets_file": os.path.join(base_dir, TARGETS_BASENAME),
        "wildcards_file": os.path.join(base_dir, WILDCARDS_BASENAME),
        "domains_file": os.path.join(base_dir, DOMAINS_BASENAME),
        "invalid_urls_file": os.path.join(base_dir, INVALID_URLS_BASENAME),
        "programs_md_file": os.path.join(base_dir, PROGRAMS_MD_BASENAME),
    }


def main():
    """Parse command-line arguments and execute the appropriate scripts."""
    parser = argparse.ArgumentParser(description="Run scripts for programs.")

    parser.add_argument("--bc", action="store_true", help="Run Bugcrowd script")
    parser.add_argument("--ywh", action="store_true", help="Run YesWeHack script")
    parser.add_argument("--h1", action="store_true", help="Run HackerOne script")
    parser.add_argument("--check-auth", action="store_true", help="Check auth before scraping")
    parser.add_argument("--dotenv", type=str, default=".env", help="Path to .env file")
    parser.add_argument("--mode", choices=["all", "new"], default="all", help="Query all programs or only newly launched ones")
    parser.add_argument("--interval", choices=["last_week", "last_month"], help="Preset interval for --mode new")
    parser.add_argument("--days", type=int, help="Custom interval in days for --mode new")

    args = parser.parse_args()

    if args.mode == "all" and (args.interval or args.days is not None):
        parser.error("--interval/--days can only be used with --mode new")

    if args.mode == "new" and args.days is not None and args.days <= 0:
        parser.error("--days must be a positive integer")

    load_dotenv(args.dotenv)
    config = load_runtime_config()
    query_options = build_query_options(args.mode, args.interval, args.days)
    paths = build_output_paths(query_options)

    if not (args.bc or args.h1 or args.ywh):
        parser.error("Please select at least one script flag: --bc, --h1, or --ywh")

    if args.check_auth:
        if args.bc and not bugcrowd.check_auth(config):
            raise SystemExit(1)
        if args.h1 and not hackerone.check_auth(config):
            raise SystemExit(1)

    program_records = []

    if args.bc:
        print("Running Bugcrowd script...")
        ensure_file_exists(paths["targets_file"])
        ensure_file_exists(paths["wildcards_file"])
        ensure_file_exists(paths["domains_file"])
        ensure_file_exists(paths["invalid_urls_file"])
        bc_records = bugcrowd.main(
            config,
            paths["targets_file"],
            paths["wildcards_file"],
            paths["domains_file"],
            paths["invalid_urls_file"],
            query_options=query_options,
        )
        if bc_records:
            program_records.extend(bc_records)

    if args.ywh:
        print("Running YesWeHack script...")
        print("YesWeHack scraper not implemented yet. Add logic in platforms/yeswehack.py")

    if args.h1:
        ensure_file_exists(paths["targets_file"])
        ensure_file_exists(paths["wildcards_file"])
        ensure_file_exists(paths["domains_file"])

        print("Running HackerOne script...")
        h1_records = hackerone.main(
            config,
            paths["targets_file"],
            paths["wildcards_file"],
            paths["domains_file"],
            query_options=query_options,
        )
        if h1_records:
            program_records.extend(h1_records)

    print("Processing output files...")
    run_post_processing(paths["wildcards_file"], paths["domains_file"], paths["invalid_urls_file"])

    ensure_file_exists(paths["programs_md_file"])
    write_programs_markdown(program_records, paths["programs_md_file"])
    print(f"Program report written to {paths['programs_md_file']}")


if __name__ == "__main__":
    main()
