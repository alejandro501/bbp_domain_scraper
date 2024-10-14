import json
import requests
import sys

def load_config(config_file):
    """Load JSON configuration from a file."""
    print(f"Loading configuration from {config_file}")
    with open(config_file, 'r') as file:
        return json.load(file)

def make_request(url, headers, json_data=None):
    """Make a request to the specified URL with optional JSON data."""
    print(f"Making request to {url} with headers {headers}")
    try:
        if json_data:
            response = requests.post(url, headers=headers, json=json_data)
        else:
            response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {url}: {e}")
        sys.exit(1)

def fetch_opportunities_with_sort_direction(api_url, headers, sort_field, sort_direction='DESC'):
    """Fetch opportunities from the API using DiscoveryQuery."""
    print(f"Fetching opportunities sorted by {sort_field} in {sort_direction} order...")
    query = {
        "operationName": "DiscoveryQuery",
        "variables": {
            "from": 0,
            "query": {},
            "filter": {
                "bool": {
                    "filter": [
                        {
                            "bool": {
                                "must_not": {
                                    "term": {"team_type": "Engagements::Assessment"}
                                },
                                "should": [
                                    {"term": {"offers_bounties": True}}
                                ]
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {"exists": {"field": "structured_scope_stats.URL"}},
                                    {"exists": {"field": "structured_scope_stats.WILDCARD"}},
                                    {"exists": {"field": "structured_scope_stats.API"}}
                                ]
                            }
                        },
                        {"range": {"minimum_low": {"gte": 1}}}
                    ]
                }
            },
            "sort": [{"field": sort_field, "direction": sort_direction}],
            "post_filters": {
                "my_programs": False,
                "bookmarked": False,
                "campaign_teams": False
            },
            "product_area": "opportunity_discovery",
            "product_feature": "search"
        },
        "query": """
        query DiscoveryQuery($query: OpportunitiesQuery!, $filter: QueryInput!, $from: Int, $size: Int, $sort: [SortInput!], $post_filters: OpportunitiesFilterInput) {
          me {
            id
            __typename
          }
          opportunities_search(
            query: $query
            filter: $filter
            from: $from
            size: $size
            sort: $sort
            post_filters: $post_filters
          ) {
            nodes {
              ... on OpportunityDocument {
                id
                handle
                __typename
              }
              __typename
            }
            __typename
          }
        }
        """
    }

    response = make_request(api_url, headers, query)

    if 'data' in response and 'opportunities_search' in response['data']:
        print("Opportunities fetched successfully.")
        return response['data']
    else:
        print("Unexpected response format:", response)
        sys.exit(1)

def fetch_opportunities_sort_desc(api_url, headers):
    """Fetch opportunities in descending order based on launched_at."""
    return fetch_opportunities_with_sort_direction(api_url, headers, sort_field='launched_at', sort_direction='DESC')

def fetch_opportunities_sort_asc(api_url, headers):
    """Fetch opportunities in ascending order based on launched_at."""
    return fetch_opportunities_with_sort_direction(api_url, headers, sort_field='launched_at', sort_direction='ASC')

def fetch_opportunities_sort_bounty_desc(api_url, headers):
    """Fetch opportunities in descending order based on minimum_bounty_table_value."""
    return fetch_opportunities_with_sort_direction(api_url, headers, sort_field='minimum_bounty_table_value', sort_direction='DESC')

def fetch_opportunities_sort_bounty_asc(api_url, headers):
    """Fetch opportunities in ascending order based on minimum_bounty_table_value."""
    return fetch_opportunities_with_sort_direction(api_url, headers, sort_field='minimum_bounty_table_value', sort_direction='ASC')

def fetch_opportunities_sort_resolved_count_desc(api_url, headers):
    """Fetch opportunities in descending order based on resolved_report_count."""
    return fetch_opportunities_with_sort_direction(api_url, headers, sort_field='resolved_report_count', sort_direction='DESC')

def fetch_opportunities_sort_resolved_count_asc(api_url, headers):
    """Fetch opportunities in ascending order based on resolved_report_count."""
    return fetch_opportunities_with_sort_direction(api_url, headers, sort_field='resolved_report_count', sort_direction='ASC')

def remove_duplicates(file_path):
    """Remove duplicate lines from the given file."""
    print(f"Removing duplicate lines from {file_path}...")
    with open(file_path, 'r') as f:
        lines = f.readlines()

    unique_lines = set(line.strip() for line in lines if line.strip())

    with open(file_path, 'w') as f:
        f.write('\n'.join(unique_lines) + '\n')
    print(f"Removed duplicates, {len(lines) - len(unique_lines)} duplicates found.")

def main(config, targets_file='targets.txt', wildcards_file='wildcards.txt', domains_file='domains.txt'):
    """Main function to execute the H1 script."""
    print("Starting H1 script...")
    graphql_url = "https://hackerone.com/graphql"

    try:
        cookie = config['credentials']['h1']['cookie']
        print("Cookie loaded successfully.")
    except KeyError as e:
        print(f"Missing key in config: {e}")
        return

    headers = {
        'Authorization': f'Bearer {cookie}',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (X11;',
        'Content-Type': 'application/json'
    }

    # Fetch opportunities in descending order (launched_at)
    opportunities_data_desc = fetch_opportunities_sort_desc(graphql_url, headers)
    handles_desc = []
    for opportunity in opportunities_data_desc['opportunities_search']['nodes']:
        handle = opportunity.get('handle')
        if handle:
            handles_desc.append(handle)
            print(f"Collected handle (DESC): {handle}")

    if handles_desc:
        with open(targets_file, 'w') as f:
            f.write('\n'.join(handles_desc) + '\n')
        print(f"Handles saved to {targets_file} (DESC) ({len(handles_desc)} collected)")
    else:
        print("No handles collected in DESC order.")

    # Fetch opportunities in ascending order (launched_at)
    opportunities_data_asc = fetch_opportunities_sort_asc(graphql_url, headers)
    handles_asc = []
    for opportunity in opportunities_data_asc['opportunities_search']['nodes']:
        handle = opportunity.get('handle')
        if handle:
            handles_asc.append(handle)
            print(f"Collected handle (ASC): {handle}")

    if handles_asc:
        with open(targets_file, 'a') as f:
            f.write('\n'.join(handles_asc) + '\n')
        print(f"Handles saved to {targets_file} (ASC) ({len(handles_asc)} collected)")
    else:
        print("No handles collected in ASC order.")

    # Fetch opportunities in descending order (minimum_bounty_table_value)
    opportunities_data_bounty_desc = fetch_opportunities_sort_bounty_desc(graphql_url, headers)
    handles_bounty_desc = []
    for opportunity in opportunities_data_bounty_desc['opportunities_search']['nodes']:
        handle = opportunity.get('handle')
        if handle:
            handles_bounty_desc.append(handle)
            print(f"Collected handle (Bounty DESC): {handle}")

    if handles_bounty_desc:
        with open(targets_file, 'a') as f:
            f.write('\n'.join(handles_bounty_desc) + '\n')
        print(f"Handles saved to {targets_file} (Bounty DESC) ({len(handles_bounty_desc)} collected)")
    else:
        print("No handles collected in Bounty DESC order.")

    # Fetch opportunities in ascending order (minimum_bounty_table_value)
    opportunities_data_bounty_asc = fetch_opportunities_sort_bounty_asc(graphql_url, headers)
    handles_bounty_asc = []
    for opportunity in opportunities_data_bounty_asc['opportunities_search']['nodes']:
        handle = opportunity.get('handle')
        if handle:
            handles_bounty_asc.append(handle)
            print(f"Collected handle (Bounty ASC): {handle}")

    if handles_bounty_asc:
        with open(targets_file, 'a') as f:
            f.write('\n'.join(handles_bounty_asc) + '\n')
        print(f"Handles saved to {targets_file} (Bounty ASC) ({len(handles_bounty_asc)} collected)")
    else:
        print("No handles collected in Bounty ASC order.")

    # Fetch opportunities in descending order (resolved_report_count)
    opportunities_data_resolved_count_desc = fetch_opportunities_sort_resolved_count_desc(graphql_url, headers)
    handles_resolved_count_desc = []
    for opportunity in opportunities_data_resolved_count_desc['opportunities_search']['nodes']:
        handle = opportunity.get('handle')
        if handle:
            handles_resolved_count_desc.append(handle)
            print(f"Collected handle (Resolved Count DESC): {handle}")

    if handles_resolved_count_desc:
        with open(targets_file, 'a') as f:
            f.write('\n'.join(handles_resolved_count_desc) + '\n')
        print(f"Handles saved to {targets_file} (Resolved Count DESC) ({len(handles_resolved_count_desc)} collected)")
    else:
        print("No handles collected in Resolved Count DESC order.")

    # Fetch opportunities in ascending order (resolved_report_count)
    opportunities_data_resolved_count_asc = fetch_opportunities_sort_resolved_count_asc(graphql_url, headers)
    handles_resolved_count_asc = []
    for opportunity in opportunities_data_resolved_count_asc['opportunities_search']['nodes']:
        handle = opportunity.get('handle')
        if handle:
            handles_resolved_count_asc.append(handle)
            print(f"Collected handle (Resolved Count ASC): {handle}")

    if handles_resolved_count_asc:
        with open(targets_file, 'a') as f:
            f.write('\n'.join(handles_resolved_count_asc) + '\n')
        print(f"Handles saved to {targets_file} (Resolved Count ASC) ({len(handles_resolved_count_asc)} collected)")
    else:
        print("No handles collected in Resolved Count ASC order.")

    # Remove duplicates from the targets file
    remove_duplicates(targets_file)

if __name__ == "__main__":
    config_file = 'config.json'
    config = load_config(config_file)
    main(config)
