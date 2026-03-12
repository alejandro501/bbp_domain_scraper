import os
import re
import time

import requests

from utils.io import read_lines_resilient


class AuthenticationError(RuntimeError):
    pass


def make_request(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError(f"Network error while requesting {url}: {exc}") from exc

    if response.status_code in (401, 403):
        raise AuthenticationError(
            f"Bugcrowd authentication failed with status {response.status_code}. Refresh your BC cookie."
        )

    return response


def generate_engagement_urls(engagements):
    base_url = "https://bugcrowd.com"
    engagement_urls = []

    for engagement in engagements:
        brief_url = engagement.get("briefUrl", "")
        if brief_url:
            full_url = f"{base_url}{brief_url}"
            engagement_urls.append(
                {
                    "name": engagement.get("name"),
                    "url": full_url,
                    "brief_url": brief_url,
                }
            )

    return engagement_urls


def extract_changelog_url(engagement_url, brief_url, headers):
    engagement_response = make_request(engagement_url, headers)

    if engagement_response.status_code != 200:
        print(f"Error fetching engagement HTML at {engagement_url}, status code: {engagement_response.status_code}")
        return None

    html_content = engagement_response.text
    start = html_content.find("/changelog/")

    if start == -1:
        print(f"Changelog URL not found in {engagement_url}")
        return None

    end = html_content.find('"', start)
    changelog_path = html_content[start:end].split("&")[0]
    if not changelog_path.endswith(".json"):
        changelog_path += ".json"

    changelog_url = f"https://bugcrowd.com{brief_url}/{changelog_path}"
    return changelog_url


def fetch_changelog_and_extract_scope(changelog_url, headers):
    changelog_response = make_request(changelog_url, headers)

    if changelog_response.status_code != 200:
        print(f"Error fetching changelog at {changelog_url}, status code: {changelog_response.status_code}")
        return []

    changelog_data = changelog_response.json()
    scope_items = changelog_data.get("data", {}).get("scope", [{}])[0].get("targets", [])

    targets = []
    accepted_categories = {"website", "api"}

    for item in scope_items:
        target_name = item.get("name")
        target_uri = item.get("uri")
        target_category = item.get("category")

        target = target_uri if target_uri else target_name
        if target and target_category in accepted_categories:
            targets.append(target)

    return targets


def check_auth(config):
    try:
        cookie = config["credentials"]["bc"]["cookie"]
    except KeyError:
        print("BC credential missing: credentials.bc.cookie")
        return False

    if not cookie:
        print("BC cookie is empty. Set BC_COOKIE in .env.")
        return False

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://bugcrowd.com/engagements",
        "Cookie": cookie,
    }

    try:
        response = make_request(
            "https://bugcrowd.com/engagements.json?category=bug_bounty&page=1&sort_by=promoted&sort_direction=desc",
            headers,
        )
    except AuthenticationError as exc:
        print(str(exc))
        return False
    except RuntimeError as exc:
        print(str(exc))
        return False

    if response.status_code != 200:
        print(f"BC auth preflight failed with status {response.status_code}")
        return False

    print("BC auth preflight succeeded.")
    return True


def main(
    config,
    targets_file="targets.txt",
    wildcards_file="wildcards.txt",
    domains_file="domains.txt",
    invalid_urls_file="invalid_urls.txt",
):
    base_url = "https://bugcrowd.com/engagements.json?category=bug_bounty&page={}&sort_by=promoted&sort_direction=desc"

    try:
        cookie = config["credentials"]["bc"]["cookie"]
    except KeyError as exc:
        print(f"Missing key in config: {exc}")
        return

    if not cookie:
        print("BC cookie is empty. Set BC_COOKIE in .env.")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Cookie": cookie,
    }

    page_number = 1
    sleep_time = 0.2
    all_targets_found = False

    with open(targets_file, "w", encoding="utf-8") as targets_file_handle:
        while not all_targets_found:
            url = base_url.format(page_number)
            headers["Referer"] = (
                f"https://bugcrowd.com/engagements?category=bug_bounty&page={page_number}&sort_by=promoted&sort_direction=desc"
            )

            try:
                response = make_request(url, headers)
            except AuthenticationError as exc:
                print(str(exc))
                break
            except RuntimeError as exc:
                print(str(exc))
                break

            if response.status_code != 200:
                print(f"Error: status code {response.status_code} for page {page_number}. Response text: {response.text}")
                break

            try:
                data = response.json()
            except ValueError as exc:
                print(f"JSON decode error: {exc}. Response text: {response.text}")
                break

            engagements = data.get("engagements", [])
            if not engagements:
                print(f"No more engagements found on page {page_number}. Stopping.")
                all_targets_found = True
                continue

            engagement_urls = generate_engagement_urls(engagements)

            for engagement in engagement_urls:
                print(f"Processing engagement: {engagement['name']}")
                try:
                    changelog_url = extract_changelog_url(engagement["url"], engagement["brief_url"], headers)
                except AuthenticationError as exc:
                    print(str(exc))
                    all_targets_found = True
                    break

                if not changelog_url:
                    print(f"Failed to get changelog URL for engagement: {engagement['name']}")
                    continue

                try:
                    scope_targets = fetch_changelog_and_extract_scope(changelog_url, headers)
                except AuthenticationError as exc:
                    print(str(exc))
                    all_targets_found = True
                    break

                for target in scope_targets:
                    targets_file_handle.write(target + "\n")

            page_number += 1
            time.sleep(sleep_time)

    process_targets_file(targets_file, wildcards_file, domains_file, invalid_urls_file)


def is_valid_url(url):
    regex = re.compile(
        r"^(?:http|ftp|wss)s?://"
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,20}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"
        r"(?::\d+)?"
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return re.match(regex, url) is not None


def process_targets_file(targets_file, wildcards_file, domains_file, invalid_urls_file):
    wildcards = []
    invalid_urls = []
    valid_urls = []

    if not os.path.isfile(targets_file):
        print(f"Error: {targets_file} does not exist.")
        return

    try:
        targets = read_lines_resilient(targets_file)
        print(f"Read {len(targets)} lines from {targets_file}")
    except Exception as exc:
        print(f"Error reading file {targets_file}: {exc}")
        return

    for target in targets:
        target = target.strip()
        if not target:
            continue

        if "*" in target:
            wildcards.append(target)
        elif not is_valid_url(target):
            invalid_urls.append(target)
        else:
            valid_urls.append(target)

    if wildcards:
        with open(wildcards_file, "w", encoding="utf-8") as wildcard_handle:
            wildcard_handle.write("\n".join(wildcards) + "\n")
        print(f"Wildcards saved to {wildcards_file} ({len(wildcards)} found)")

    if invalid_urls:
        with open(invalid_urls_file, "w", encoding="utf-8") as invalid_handle:
            invalid_handle.write("\n".join(invalid_urls) + "\n")
        print(f"Invalid URLs saved to {invalid_urls_file} ({len(invalid_urls)} found)")

    if valid_urls:
        with open(domains_file, "w", encoding="utf-8") as valid_handle:
            valid_handle.write("\n".join(valid_urls) + "\n")
        print(f"Valid URLs saved to {domains_file} ({len(valid_urls)} found)")
