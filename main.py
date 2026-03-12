import argparse
import os

from config.settings import load_dotenv, load_runtime_config
from platforms import bugcrowd, hackerone
from utils import post_digest


def ensure_file_exists(file_path):
    """Ensure that a file exists; if not, create it."""
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


def main():
    """Parse command-line arguments and execute the appropriate scripts."""
    parser = argparse.ArgumentParser(description="Run scripts for programs.")

    parser.add_argument("--bc", action="store_true", help="Run Bugcrowd script")
    parser.add_argument("--ywh", action="store_true", help="Run YesWeHack script")
    parser.add_argument("--h1", action="store_true", help="Run HackerOne script")
    parser.add_argument("--check-auth", action="store_true", help="Check auth before scraping")
    parser.add_argument("--dotenv", type=str, default=".env", help="Path to .env file")
    parser.add_argument("--targets_file", type=str, default="targets.txt", help="Output file for targets")
    parser.add_argument("--wildcards_file", type=str, default="wildcards.txt", help="Wildcards file")
    parser.add_argument("--domains_file", type=str, default="domains.txt", help="Output file for domains")
    parser.add_argument("--invalid_urls_file", type=str, default="invalid_urls.txt", help="Output file for invalid URLs")

    args = parser.parse_args()

    load_dotenv(args.dotenv)
    config = load_runtime_config()

    if not (args.bc or args.h1 or args.ywh):
        parser.error("Please select at least one script flag: --bc, --h1, or --ywh")

    if args.check_auth:
        if args.bc and not bugcrowd.check_auth(config):
            raise SystemExit(1)
        if args.h1 and not hackerone.check_auth(config):
            raise SystemExit(1)

    if args.bc:
        print("Running Bugcrowd script...")
        bugcrowd.main(config, args.targets_file, args.wildcards_file, args.domains_file, args.invalid_urls_file)

    if args.ywh:
        print("Running YesWeHack script...")
        print("YesWeHack scraper not implemented yet. Add logic in platforms/yeswehack.py")

    if args.h1:
        ensure_file_exists(args.targets_file)
        ensure_file_exists(args.wildcards_file)
        ensure_file_exists(args.domains_file)

        print("Running HackerOne script...")
        hackerone.main(config, args.targets_file, args.wildcards_file, args.domains_file)

    print("Processing output files...")
    run_post_processing(args.wildcards_file, args.domains_file, args.invalid_urls_file)


if __name__ == "__main__":
    main()
