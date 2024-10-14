import argparse
import json
import os
import bc
import h1
import url_post_digest

def load_config(config_file):
    """Load JSON configuration from a file."""
    print(f"Loading configuration from {config_file}")
    with open(config_file, 'r') as file:
        return json.load(file)

def ensure_file_exists(file_path):
    """Ensure that a file exists; if not, create it."""
    if not os.path.exists(file_path):
        print(f"Creating empty file: {file_path}")
        with open(file_path, 'w') as f:
            pass  # Create an empty file

def main():
    """Parse command-line arguments and execute the appropriate scripts."""
    parser = argparse.ArgumentParser(description="Run scripts for programs.")
    
    parser.add_argument('--bc', action='store_true', help='Run BC script')
    parser.add_argument('--ywh', action='store_true', help='Run YWH script')
    parser.add_argument('--h1', action='store_true', help='Run H1 script')
    parser.add_argument('--config', '-C', type=str, required=True, help='JSON config file')
    parser.add_argument('--targets_file', type=str, default='targets.txt', help='Output file for targets')
    parser.add_argument('--wildcards_file', type=str, default='wildcards.txt', help='Wildcards file')
    parser.add_argument('--domains_file', type=str, default='domains.txt', help='Output file for domains')
    parser.add_argument('--invalid_urls_file', type=str, default='invalid_urls.txt', help='Output file for invalid URLs')

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Run Bugcrowd script if specified
    if args.bc:
        if os.path.exists(args.targets_file) or os.path.exists(args.domains_file) or os.path.exists(args.invalid_urls_file):
            print(f"Skipping BC script execution; output files already exist: {args.targets_file}, {args.domains_file}, {args.invalid_urls_file}")
        else:
            print("Running BC script...")
            bc.main(config, args.targets_file, args.domains_file, args.invalid_urls_file)

    # Run YWH script if specified
    if args.ywh:
        print("Running YWH script...")
        # ywh.main(config)  # Uncomment when ywh.py is available

    # Run H1 script if specified
    if args.h1:
        # Ensure the required files exist
        ensure_file_exists(args.targets_file)
        ensure_file_exists(args.wildcards_file)
        ensure_file_exists(args.domains_file)

        print("Running H1 script...")
        h1.main(config, args.targets_file, args.wildcards_file, args.domains_file)

    # Clean up and process the output files after H1 execution
    print("Processing output files...")
    url_post_digest.clean_wildcards(args.wildcards_file, args.domains_file)
    url_post_digest.clean_invalid_urls(args.invalid_urls_file, args.domains_file)
    url_post_digest.add_https_to_domains(args.domains_file)
    url_post_digest.remove_duplicate_domains(args.domains_file)

if __name__ == "__main__":
    main()
