# main.py
import argparse
import json
import bc  # Assuming bc refers to the Bugcrowd script

def load_config(config_file):
    """ Load JSON configuration from a file. """
    with open(config_file, 'r') as file:
        return json.load(file)

def main():
    # Command-line arguments
    parser = argparse.ArgumentParser(description="Run scripts for programs.")
    parser.add_argument('--bc', action='store_true', help='Run Bc script')
    parser.add_argument('--ywh', action='store_true', help='Run YWH script')
    parser.add_argument('--h1', action='store_true', help='Run H1 script')
    parser.add_argument('--config', '-C', type=str, required=True, help='JSON config file')

    args = parser.parse_args()

    # Default to Bugcrowd if no script is specified
    if not (args.bc or args.ywh or args.h1):
        args.bc = True  

    config = load_config(args.config)

    if args.bc:
        print("Running BC script with config...")
        bc.main(config)

    if args.ywh:
        print("Running YWH script with config...")
        # ywh.main(config)  # Uncomment when ywh.py is available

    if args.h1:
        print("Running H1 script with config...")
        # h1.main(config)  # Uncomment when h1.py is available

if __name__ == "__main__":
    main()
