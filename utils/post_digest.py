import os
import re


def create_trash_dir(trash_dir="domain_trash"):
    """Create the backup directory if it does not exist."""
    os.makedirs(trash_dir, exist_ok=True)


def backup_original_file(original_file, trash_filename):
    """Backup source file before modification, if it exists."""
    if not os.path.isfile(original_file):
        return

    base_dir = os.path.dirname(original_file) or "."
    trash_dir = os.path.join(base_dir, "domain_trash")
    create_trash_dir(trash_dir)
    original_trash_path = os.path.join(trash_dir, trash_filename)

    with open(original_file, "r", encoding="utf-8", errors="replace") as src_file:
        original_content = src_file.read()
    with open(original_trash_path, "w", encoding="utf-8") as backup_file:
        backup_file.write(original_content)


def clean_wildcards(wildcards_file, domains_file):
    """Process wildcards, normalize them, and append eligible domains."""
    if not os.path.isfile(wildcards_file):
        print(f"{wildcards_file} does not exist. Skipping...")
        return

    backup_original_file(wildcards_file, "wildcards_original.txt")
    cleaned_wildcards = []
    domains_to_add = []

    with open(wildcards_file, "r", encoding="utf-8", errors="replace") as file:
        for line in file:
            line = line.strip()
            line = line.lstrip("*").lstrip(".").lstrip("-").strip()
            if line.endswith("*"):
                domains_to_add.append(line[:-1].strip())
                continue
            line = re.sub(r"^[a-zA-Z]+://", "", line)
            if line and (line[0].isalpha() or line[0].isdigit()):
                cleaned_wildcards.append(line)

    with open(wildcards_file, "w", encoding="utf-8") as file:
        for wildcard in cleaned_wildcards:
            file.write(wildcard + "\n")

    with open(domains_file, "a", encoding="utf-8") as file:
        for domain in domains_to_add:
            if domain:
                file.write(domain + "\n")

    print("Processed wildcards and saved additional domains.")


def clean_invalid_urls(invalid_urls_file, domains_file):
    """Clean invalid URLs and append probable domains."""
    if not os.path.isfile(invalid_urls_file):
        print(f"{invalid_urls_file} does not exist. Skipping...")
        return

    backup_original_file(invalid_urls_file, "invalid_urls_original.txt")
    domains = []

    with open(invalid_urls_file, "r", encoding="utf-8", errors="replace") as file:
        for line in file:
            line = line.strip()
            if "." in line and " " not in line:
                domains.append("https://" + line)

    with open(domains_file, "a", encoding="utf-8") as file:
        for domain in domains:
            file.write(domain + "\n")

    print("Processed invalid URLs and saved domains.")


def add_https_to_domains(domains_file):
    """Add https to domains that are missing protocol."""
    if not os.path.isfile(domains_file):
        print(f"{domains_file} does not exist. Skipping...")
        return

    backup_original_file(domains_file, "domains_original.txt")
    updated_domains = []

    with open(domains_file, "r", encoding="utf-8", errors="replace") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            if not line.startswith("http://") and not line.startswith("https://"):
                updated_domains.append(f"https://{line}")
            else:
                updated_domains.append(line)

    with open(domains_file, "w", encoding="utf-8") as file:
        for domain in updated_domains:
            file.write(domain + "\n")

    print("Updated domains with https protocol where missing.")


def remove_duplicate_domains(domains_file):
    """Remove duplicate lines from domains file."""
    if not os.path.isfile(domains_file):
        print(f"{domains_file} does not exist. Skipping...")
        return

    backup_original_file(domains_file, "domains_duplicates_original.txt")
    with open(domains_file, "r", encoding="utf-8", errors="replace") as source_file:
        unique_domains = sorted({line.strip() for line in source_file if line.strip()})

    with open(domains_file, "w", encoding="utf-8") as file:
        for domain in unique_domains:
            file.write(domain + "\n")

    print("Removed duplicate domains from the domains file.")
