import argparse
import bbp_domain_scraper.bc as bc 

def main():
    # args
    parser = argparse.ArgumentParser(description="Run Bugcrowd scripts.")
    parser.add_argument('--bc', action='store_true', help='Run Bugcrowd script')
    parser.add_argument('--ywh', action='store_true', help='Run YWH script')
    parser.add_argument('--h1', action='store_true', help='Run H1 script')

    args = parser.parse_args()

    if not (args.bc or args.ywh or args.h1):
        #args.bc = args.ywh = args.h1 = True
        args.bc = True # only running bc so far since others are not developed yet.

    # Run the Bugcrowd script if --bc is specified
    if args.bc:
        print("Running BC script...")
        bc.main()  # Call the main function from bugcrowd.py

    # Placeholder for YWH script
    if args.ywh:
        print("Running YWH script...")
        # ywh.main()  # when ywh.py is available

    # Placeholder for H1 script
    if args.h1:
        print("Running H1 script...")
        # h1.main()  # when h1.py is available

if __name__ == "__main__":
    main()
