import argparse
import json
import os
import bc
import url_post_digest

def load_config(config_file):
    """Load JSON configuration from a file."""
    with open(config_file, 'r') as file:
        return json.load(file)

def main():
    """Parse command-line arguments and execute the appropriate scripts."""
    parser = argparse.ArgumentParser(description="Run scripts for programs.")
    parser.add_argument('--bc', action='store_true', help='Run BC script')
    parser.add_argument('--ywh', action='store_true', help='Run YWH script')
    parser.add_argument('--h1', action='store_true', help='Run H1 script')
    parser.add_argument('--config', '-C', type=str, required=True, help='JSON config file')
    parser.add_argument('--targets_file', type=str, default='targets.txt', help='Output file for targets')
    parser.add_argument('--wildcards_file', type=str, default='wildcards.txt', help='Wildcards')
    parser.add_argument('--domains_file', type=str, default='domains.txt', help='Output file for domains')
    parser.add_argument('--invalid_urls_file', type=str, default='invalid_urls.txt', help='Output file for invalid URLs')

    args = parser.parse_args()

    if not (args.bc or args.ywh or args.h1):
        args.bc = True  

    config = load_config(args.config)

    if args.bc:
        if os.path.exists(args.targets_file) or os.path.exists(args.domains_file) or os.path.exists(args.invalid_urls_file):
            print(f"Skipping BC script execution; output files already exist: {args.targets_file}, {args.domains_file}, {args.invalid_urls_file}")
        else:
            print("Running BC script with config...")
            bc.main(config, args.targets_file, args.domains_file, args.invalid_urls_file)

    if args.ywh:
        if os.path.exists(args.domains_file):
            print("Skipping YWH script execution; output file already exists.")
        else:
            print("Running YWH script with config...")
            # ywh.main(config)  # Uncomment when ywh.py is available

    if args.h1:
        if os.path.exists(args.domains_file):
            print("Skipping H1 script execution; output file already exists.")
        else:
            print("Running H1 script with config...")
            # h1.main(config)  # Uncomment when h1.py is available

    url_post_digest.clean_wildcards(args.wildcards_file, args.domains_file)
    url_post_digest.clean_invalid_urls(args.invalid_urls_file, args.domains_file)
    url_post_digest.add_https_to_domains(args.domains_file)

if __name__ == "__main__":
    main()
