import os
import re

import os
import re

import os
import re

def clean_wildcards(wildcards_file, domains_file):
    # Create domain_trash directory if it doesn't exist
    trash_dir = 'domain_trash'
    os.makedirs(trash_dir, exist_ok=True)

    # Save the original wildcards file in domain_trash
    original_wildcards_path = os.path.join(trash_dir, 'wildcards_original.txt')
    with open(wildcards_file, 'r') as original_wildcards_file:
        original_content = original_wildcards_file.read()
    
    with open(original_wildcards_path, 'w') as original_wildcards_file:
        original_wildcards_file.write(original_content)

    # Prepare to read and process the wildcards
    cleaned_wildcards = []
    domains_to_add = []

    with open(wildcards_file, 'r') as f:
        for line in f:
            line = line.strip()

            # Remove leading asterisks, dots, and hyphens
            line = line.lstrip('*').lstrip('.').lstrip('-').strip()

            # If the line has an asterisk at the end, prepare to add to domains
            if line.endswith('*'):
                domains_to_add.append(line[:-1].strip())  # Remove the trailing '*'
                continue

            # Remove protocols if present
            line = re.sub(r'^[a-zA-Z]+://', '', line)

            # Validate that the cleaned line starts with a letter or number
            if line and (line[0].isalpha() or line[0].isdigit()):
                cleaned_wildcards.append(line)

    # Write cleaned wildcards back to wildcards.txt
    with open(wildcards_file, 'w') as f:
        for wildcard in cleaned_wildcards:
            f.write(wildcard + '\n')

    # Append new domains to the existing domains file
    with open(domains_file, 'a') as f:
        for domain in domains_to_add:
            if domain:  # Ensure not to write empty domains
                f.write(domain + '\n')

    print("Processed wildcards and saved additional domains.")


def clean_invalid_urls(invalid_urls_file, domains_file):
    # Create domain_trash directory if it doesn't exist
    trash_dir = 'domain_trash'
    os.makedirs(trash_dir, exist_ok=True)

    # Save the original invalid URLs file in domain_trash
    original_invalid_urls_path = os.path.join(trash_dir, 'invalid_urls_original.txt')
    with open(invalid_urls_file, 'r') as original_invalid_urls_file:
        original_content = original_invalid_urls_file.read()
    
    with open(original_invalid_urls_path, 'w') as original_invalid_urls_file:
        original_invalid_urls_file.write(original_content)

    # Prepare to read and process the invalid URLs
    domains = []

    with open(invalid_urls_file, 'r') as f:
        for line in f:
            line = line.strip()
            # Check if the line looks like a URL (contains a dot and has no spaces)
            if '.' in line and ' ' not in line:
                # Add https:// to the line and append to domains list
                domains.append('https://' + line)

    # Write cleaned domains to the specified domains file
    with open(domains_file, 'a') as f:  # Append to the domains file
        for domain in domains:
            f.write(domain + '\n')

    print("Processed invalid URLs and saved domains.")

# Main method for testing purposes
if __name__ == "__main__":
    # Example usage
    clean_wildcards('path/to/wildcards.txt', 'path/to/domains.txt')
    clean_invalid_urls('path/to/invalid_urls.txt', 'path/to/domains.txt')
