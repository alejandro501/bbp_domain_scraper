import sys
import os
import requests
import json
import time
import re

# Load credentials from config.json
def load_config(config_file):
    with open(config_file, 'r') as file:
        return json.load(file)

# Make request
def make_request(url, headers, cookies):
    response = requests.get(url, headers=headers, cookies={'cookie': cookies})
    return response

# Call 1: Generate engagement URLs
def generate_engagement_urls(engagements):
    base_url = "https://bugcrowd.com"
    engagement_urls = []

    for engagement in engagements:
        brief_url = engagement.get('briefUrl', '')
        if brief_url:
            full_url = f"{base_url}{brief_url}"
            engagement_urls.append({
                'name': engagement.get('name'),
                'url': full_url,
                'brief_url': brief_url
            })

    return engagement_urls

# Call 2. Extract changelog URL from the engagement HTML content
def extract_changelog_url(engagement_url, brief_url, headers, cookies):
    engagement_response = make_request(engagement_url, headers, cookies)
    
    if engagement_response.status_code == 200:
        html_content = engagement_response.text
        start = html_content.find('/changelog/')
        
        if start != -1:
            end = html_content.find('"', start)
            changelog_path = html_content[start:end]
            changelog_path = changelog_path.split('&')[0]
            
            if not changelog_path.endswith('.json'):
                changelog_path += '.json'
            
            changelog_url = f"https://bugcrowd.com{brief_url}/{changelog_path}"
            return changelog_url
        else:
            print(f"Changelog URL not found in {engagement_url}")
            return None
    else:
        print(f"Error fetching engagement HTML at {engagement_url}, status code: {engagement_response.status_code}")
        return None
    
# Call 3. Fetch changelog and extract scope data
def fetch_changelog_and_extract_scope(changelog_url, headers, cookies):
    changelog_response = make_request(changelog_url, headers, cookies)
    if changelog_response.status_code == 200:
        changelog_data = changelog_response.json()
        scope_items = changelog_data['data']['scope'][0]['targets']
        
        targets = []
        accepted_categories = {'website', 'api'}  # Only process website and api in scope
        
        for item in scope_items:
            target_name = item.get('name')
            target_uri = item.get('uri')
            target_category = item.get('category')
            
            # Prioritize URI if present, else fallback to name
            target = target_uri if target_uri else target_name
            
            if target and target_category in accepted_categories:
                targets.append(target)
            
        return targets
    else:
        print(f"Error fetching changelog at {changelog_url}, status code: {changelog_response.status_code}")
        return []

# Main function to fetch engagements and extract scope targets
def main(config):
    base_url = "https://bugcrowd.com/engagements.json?category=bug_bounty&page={}&sort_by=promoted&sort_direction=desc"

    """ Main function for Bugcrowd script using the loaded config. """
    try:
        cookies = config['credentials']['bc']['cookie']

    except KeyError as e:
        print(f"Missing key in config: {e}")
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://bugcrowd.com/engagements?category=bug_bounty&page={}&sort_by=promoted&sort_direction=desc',
        'Connection': 'keep-alive'
    }

    page_number = 1
    sleep_time = 0.2
    all_targets_found = False

    with open('targets.txt', 'w') as targets_file:
        while not all_targets_found:  # Fetch engagements
            filename = f'engagements_{page_number}.json'

            if os.path.exists(filename):
                print(f"{filename} already exists. Skipping page {page_number}.")
                page_number += 1
                continue

            url = base_url.format(page_number)
            headers['Referer'] = headers['Referer'].format(page_number)
            response = make_request(url, headers, cookies)

            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError as e:
                    print(f"JSON decode error: {e}. Response text: {response.text}")
                    break

                engagements = data.get('engagements', [])

                if not engagements:
                    print(f"No more engagements found on page {page_number}. Stopping.")
                    all_targets_found = True
                    continue

                with open(filename, 'w', encoding='utf-8') as file:
                    json.dump(data, file, indent=4)
                print(f"Response body saved to {filename}")

                engagement_urls = generate_engagement_urls(engagements)

                for engagement in engagement_urls:
                    print(f"Processing engagement: {engagement['name']}")

                    changelog_url = extract_changelog_url(engagement['url'], engagement['brief_url'], headers, cookies)
                    
                    if changelog_url:  
                        scope_targets = fetch_changelog_and_extract_scope(changelog_url, headers, cookies)
                        
                        for target in scope_targets:
                            targets_file.write(target + "\n")
                    else:
                        print(f"Failed to get changelog URL for engagement: {engagement['name']}")

                page_number += 1
                time.sleep(sleep_time)
            else:
                print(f"Error: status code {response.status_code} for page {page_number}. Response text: {response.text}")
                all_targets_found = True
                break

    # After all targets are fetched, process the targets file
    process_targets_file('targets.txt')
    
# Check if a string is a valid URL
def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp|wss)s?://'  # http://, https://, ftp://, wss://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,20}\.?|[A-Z0-9-]{2,}\.?)|'  # Domain name
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # IPv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # IPv6
        r'(?::\d+)?'  # Optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # Optional path
    return re.match(regex, url) is not None

# 4. Processing complete targets.txt file to separate them into`wildcards.txt`, `domains.txt` and `invalid_urls.txt`
def process_targets_file(targets_file):
    if not os.path.isfile(targets_file):
        print(f"Error: {targets_file} does not exist.")
        return

    wildcards = []
    invalid_urls = []
    valid_urls = []

    try:
        with open(targets_file, 'r', encoding='utf-8') as file:
            targets = file.readlines()
            print(f"Content of {targets_file} (first 10 lines):")
            print("".join(targets[:10]))  # Print the first 10 lines for review

    except UnicodeDecodeError:
        print(f"Error: Could not decode {targets_file} with UTF-8. Trying ISO-8859-1 encoding.")
        try:
            with open(targets_file, 'r', encoding='ISO-8859-1') as file:
                targets = file.readlines()
                print(f"Content of {targets_file} (first 10 lines):")
                print("".join(targets[:10]))
        except Exception as e:
            print(f"Error reading file {targets_file} with ISO-8859-1: {e}")
            return
    except Exception as e:
        print(f"Error reading file {targets_file}: {e}")
        return

    print(f"Total targets read: {len(targets)}")

    for target in targets:
        target = target.strip() 
        if not target: 
            continue

        print(f"Processing target: {repr(target)}") 

        if '*' in target: 
            wildcards.append(target)
        elif not is_valid_url(target):
            invalid_urls.append(target)
        else: 
            valid_urls.append(target)

    # Writing to output files...
    if wildcards:
        with open('wildcards.txt', 'w') as wildcard_file:
            wildcard_file.write('\n'.join(wildcards) + '\n')
        print(f"Wildcards saved to wildcards.txt ({len(wildcards)} found)")

    if invalid_urls:
        with open('invalid_urls.txt', 'w') as invalid_file:
            invalid_file.write('\n'.join(invalid_urls) + '\n')
        print(f"Invalid URLs saved to invalid_urls.txt ({len(invalid_urls)} found)")

    if valid_urls:
        with open('valid_urls.txt', 'w') as valid_file:
            valid_file.write('\n'.join(valid_urls) + '\n')
        print(f"Valid URLs saved to valid_urls.txt ({len(valid_urls)} found)")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the config file.")
        sys.exit(1)
    config = load_config(sys.argv[1])
    main(config)
