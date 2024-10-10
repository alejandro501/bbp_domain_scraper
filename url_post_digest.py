import os
import re

def create_trash_dir(trash_dir='domain_trash'):
    """Creates the domain_trash directory if it doesn't exist."""
    os.makedirs(trash_dir, exist_ok=True)

def backup_original_file(original_file, trash_filename):
    """Backs up the original file to the domain_trash directory."""
    trash_dir = 'domain_trash'
    create_trash_dir(trash_dir)
    original_trash_path = os.path.join(trash_dir, trash_filename)
    with open(original_file, 'r') as src_file:
        original_content = src_file.read()
    with open(original_trash_path, 'w') as backup_file:
        backup_file.write(original_content)

def clean_wildcards(wildcards_file, domains_file):
    """Processes wildcards, removes unnecessary characters, and appends domains."""
    backup_original_file(wildcards_file, 'wildcards_original.txt')
    cleaned_wildcards = []
    domains_to_add = []
    with open(wildcards_file, 'r') as f:
        for line in f:
            line = line.strip()
            line = line.lstrip('*').lstrip('.').lstrip('-').strip()
            if line.endswith('*'):
                domains_to_add.append(line[:-1].strip())
                continue
            line = re.sub(r'^[a-zA-Z]+://', '', line)
            if line and (line[0].isalpha() or line[0].isdigit()):
                cleaned_wildcards.append(line)
    with open(wildcards_file, 'w') as f:
        for wildcard in cleaned_wildcards:
            f.write(wildcard + '\n')
    with open(domains_file, 'a') as f:
        for domain in domains_to_add:
            if domain:
                f.write(domain + '\n')
    print("Processed wildcards and saved additional domains.")

def clean_invalid_urls(invalid_urls_file, domains_file):
    """Cleans invalid URLs, adds https if needed, and appends them to domains."""
    backup_original_file(invalid_urls_file, 'invalid_urls_original.txt')
    domains = []
    with open(invalid_urls_file, 'r') as f:
        for line in f:
            line = line.strip()
            if '.' in line and ' ' not in line:
                domains.append('https://' + line)
    with open(domains_file, 'a') as f:
        for domain in domains:
            f.write(domain + '\n')
    print("Processed invalid URLs and saved domains.")

def add_https_to_domains(domains_file):
    """Adds https to domains that are missing a protocol."""
    backup_original_file(domains_file, 'domains_original.txt')
    updated_domains = []
    with open(domains_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line.startswith('http://') and not line.startswith('https://'):
                updated_domains.append(f'https://{line}')
            else:
                updated_domains.append(line)
    with open(domains_file, 'w') as f:
        for domain in updated_domains:
            f.write(domain + '\n')
    print("Updated domains with https protocol where missing.")

def remove_duplicate_domains(domains_file):
    """Removes duplicate lines from the domains file."""
    backup_original_file(domains_file, 'domains_duplicates_original.txt')
    unique_domains = set()
    with open(domains_file, 'r') as f:
        for line in f:
            unique_domains.add(line.strip())
    with open(domains_file, 'w') as f:
        for domain in unique_domains:
            f.write(domain + '\n')
    print("Removed duplicate domains from the domains file.")

if __name__ == "__main__":
    clean_wildcards('path/to/wildcards.txt', 'path/to/domains.txt')
    clean_invalid_urls('path/to/invalid_urls.txt', 'path/to/domains.txt')
    add_https_to_domains('path/to/domains.txt')
    remove_duplicate_domains('path/to/domains.txt')
