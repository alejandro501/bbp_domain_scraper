import json
import requests
import sys

def load_config(config_file):
    """Load JSON configuration from a file."""
    with open(config_file, 'r') as file:
        return json.load(file)

def make_request(url, headers, json_data=None):
    """Make a request to the specified URL with optional JSON data."""
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

def fetch_identifiers_for_handle(api_url, headers, handle):
    """Fetch identifiers for a given handle using PolicySearchStructuredScopesQuery."""
    print(f"Fetching identifiers for handle: {handle}")
    
    # Query structure
    query = {
        "operationName": "PolicySearchStructuredScopesQuery",
        "variables": {
            "handle": handle,
            "searchString": "",
            "eligibleForSubmission": None,
            "eligibleForBounty": None,
            "asmTagIds": [],
            "assetTypes": [],
            "from": 0,
            "size": 100,
            "sort": {"field": "cvss_score", "direction": "DESC"},
            "product_area": "h1_assets",
            "product_feature": "policy_scopes"
        },
        "query": """
        query PolicySearchStructuredScopesQuery(
            $handle: String!,
            $searchString: String,
            $eligibleForSubmission: Boolean,
            $eligibleForBounty: Boolean,
            $minSeverityScore: SeverityRatingEnum,
            $asmTagIds: [Int],
            $assetTypes: [StructuredScopeAssetTypeEnum!],
            $from: Int,
            $size: Int,
            $sort: SortInput
        ) {
          team(handle: $handle) {
            id
            team_display_options {
              show_total_reports_per_asset
              __typename
            }
            structured_scopes_search(
              search_string: $searchString
              eligible_for_submission: $eligibleForSubmission
              eligible_for_bounty: $eligibleForBounty
              min_severity_score: $minSeverityScore
              asm_tag_ids: $asmTagIds
              asset_types: $assetTypes
              from: $from
              size: $size
              sort: $sort
            ) {
              nodes {
                ... on StructuredScopeDocument {  # Correct type name
                  id
                  ...PolicyScopeStructuredScopeDocument
                  __typename
                }
                __typename
              }
              pageInfo {
                startCursor
                hasPreviousPage
                endCursor
                hasNextPage
                __typename
              }
              total_count
              __typename
            }
            __typename
          }
        }

        fragment PolicyScopeStructuredScopeDocument on StructuredScopeDocument {
          id
          identifier
          display_name
          instruction
          cvss_score
          eligible_for_bounty
          eligible_for_submission
          asm_system_tags
          created_at
          updated_at
          total_resolved_reports
          attachments {
            id
            file_name
            file_size
            content_type
            expiring_url
            __typename
          }
          __typename
        }
        """
    }

    response = make_request(api_url, headers, query)

    if 'data' in response and 'team' in response['data']:
        return response['data']['team']['structured_scopes_search']['nodes']
    else:
        print(f"Unexpected response format for handle {handle}: {response}")
        return []

def collect_identifiers_from_targets(api_url, headers, targets_file='targets.txt', wildcards_file='wildcards.txt', domains_file='domains.txt'):
    """Collect identifiers from handles in targets.txt and save them into wildcards.txt and domains.txt."""
    with open(targets_file, 'r') as f:
        handles = f.read().splitlines()

    wildcards = []
    domains = []

    for handle in handles:
        identifiers = fetch_identifiers_for_handle(api_url, headers, handle)
        for item in identifiers:
            identifier = item.get('identifier')
            if identifier:             
                if item['display_name'] in ["Domain", "Url"]:
                    domains.append(identifier)
                elif item['display_name'] == "Wildcard":
                    wildcards.append(identifier)
                
    # Save results to files
    with open(wildcards_file, 'w') as f:
        f.write('\n'.join(wildcards) + '\n')
    print(f"Wildcards saved to {wildcards_file} ({len(wildcards)} collected)")

    with open(domains_file, 'w') as f:
        f.write('\n'.join(domains) + '\n')
    print(f"Domains saved to {domains_file} ({len(domains)} collected)")

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
        handles_desc.append(opportunity['handle'])

    # Collect identifiers for descending order
    collect_identifiers_from_targets(graphql_url, headers, targets_file=targets_file, wildcards_file=wildcards_file, domains_file=domains_file)

    # Optionally remove duplicates
    remove_duplicates(wildcards_file)
    remove_duplicates(domains_file)

if __name__ == "__main__":
    config_file_path = 'config.json'
    config = load_config(config_file_path)
    main(config)
