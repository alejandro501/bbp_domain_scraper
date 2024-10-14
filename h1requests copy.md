this is my code:
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

as you can see i've collected handles into targets.txt

now i want to iterate the  handles/lines in targets.txt so i can collect the identifies for each of them into wildcards.txt and domains.txt

example request I need to use:


request:
POST /graphql HTTP/2
Host: hackerone.com
Cookie: h1_device_id=b43e6781-b416-44b7-91fd-1c85ec374a08; __Host-session=UElpRFora2NYd3FkK1lZV1lYWkRZUUlnTFpCQlRLMzVSRnUxN0hkRDNlOVN3cmpHdFZCK3pVRC9sSUVReTNnRy9IV3J4T3NSaDhaQzZqL1VPZlk2UUhCSmpPRmtpcUkyTEt2eHdWeUxxa1FLdjJZTzE3dWhUd2NINERZUHd3blFSQVFrVEtiVW1oRmVCRGppY0EvOHBzbkNseG5pL2hhM1pMVXVhbUoyZHg0NncrMEpSWU1sQmxvUVN0OHhTc2d4VnlLUmtlRDRrMklrNFZLWmFXYWpld0taeUJaTEc2cURJWDY2NktKT1V6NGNLTGpYWFp6OU9OZU4yYU1pU2ZkKzJzeEJTekJ1V2kzTlNZMmcwNi8xM1pTeU96eDhKSy9sOFFVZ2dYQzdVSmdmcXFTL2pRRnBMbyt4MTYzL0Z1QXRtbWpUWFBOQm9sQjZlWG5jSVlIMVdxMFJLd3JCN3g0RU45RW1UcndlTzFBa2phbVh4NEVVK1M5UnRNd0RQT1RwZmlqSjRvalhsYmxYbThwQ2xXRkp1a29PQ1U0N1VGNDhhRjR5MkNVQ0ZEb0VKZTc1K3R4d2FiZnhtQ0x4bUl2STRsb05kZE5iejNjUERUamJHc2ZrSWU2TW82UUR2aUtOYk1CNDdLYVE3WnVoVTh5TTJidWxRaktJVzdhV3NSdEZpUFFJS1BFUTVyWGwyOHNRcWMxRkxvOVY2L1VNUkVTbUw4NjBYZGVVMkg2T1pFM0x5SmlCcFBwVUpJN1R3eDdNaXdENnQ5MzBWN3pJbmFpRGh0Mi96cG5XdWQvOGFLZnhrdS9kSEgvSm5hTkZENThxc256dHJ1WU1WUmZ5YzhSbmdta0tvRTNoTUdXV1VoeDl6UjR4NXZGWldlMkVoU3NaSUg2QXJxazhoVnBjN2p3K1hvQ25IaU1jZTVsNHdmL3AtLVBxR0Y5VnBxOXRMYTdqQThEaHBzc0E9PQ%3D%3D--5d548f446fd2f2ef3aae3c8a045693d08ba9a612; _cfuvid=pTUekJMfuUVNhMf7HXQhql7fAdvokrGDP9XbYxEf6Bg-1728638814604-0.0.1.1-604800000; optimizelyEndUserId=oeu1728638815646r0.07158869887990593; cf_clearance=V5GPIrX8RAbjif.FoPhSN74bY8kKjH80g79hJHMqHYo-1728638817-1.2.1.1-PGfTbvIpK0mAkBfzi4jOMUjMyzXc6a5l_KOjDlNeSRBI8oyXW4k0l9DDS5IOSk74gPAzOHeQD4FmSDJeIOqabqJJS1isV0nxeQP.FhIxEGU5R.JLm_9wYze7WuoSBYGFApDe4Oml74I.Nj1EzuZZ6X51ygETVEnCfZNDrVUZEDHCx2E52nJqMzWb3IInQdEzCmd1Zq.yEnVuLutUjCCqSbJqcfI_zgkeMryfPvuKnc6rA03qkpU2rZgUherhx3pzZIK_MKMd3yN4XSa.d5crQY0FXdFnLLBTZD0yWog_8eBbE95o.PAwqgwFlPJN2zJ5Yy.MIE.ZfeE7c3a2fjH_qMndOROmLILh8kKDwcvFvcObMbJrhLOmIq_ibETxDBM1; _dd_s=rum=2&id=42571c06-9294-4832-93d4-079e77c8e690&created=1728638825457&expire=1728640178685; app_signed_in=true; intercom-session-zlmaz2pu=RXErV1dkZXE5MEhrNGprNmpaT2ttT0h6MmZEemR1VDVjR1prczNrNHRueDNvTHhBY2RlRmNKSk02U0ZBaXp5TC0ta01QaGYrY0NXRUlJWTczMndOL0ZJdz09--ace745f18ac981d3196db132437831ed1daf83cd; intercom-device-id-zlmaz2pu=4969a6d4-02d6-4d0a-89fa-2f767621720b
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0
Accept: */*
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: https://hackerone.com/bitso/policy_scopes
Content-Type: application/json
X-Csrf-Token: CMiLVfbbdv0n3dmTKwCkMokeyd+iSAgMTSTi4N0l09EKxOZcbr3K0tyVV67IG8DLz4qsoYKoWqzPLC5GtV+BYg==
X-Product-Area: h1_assets
X-Product-Feature: policy_scopes
X-Datadog-Origin: rum
X-Datadog-Parent-Id: 9153046296999258707
X-Datadog-Sampling-Priority: 1
X-Datadog-Trace-Id: 8815370431741775596
Content-Length: 1863
Origin: https://hackerone.com
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
Dnt: 1
Sec-Gpc: 1
Priority: u=0
Te: trailers

{"operationName":"PolicySearchStructuredScopesQuery","variables":{"handle":"bitso","searchString":"","eligibleForSubmission":null,"eligibleForBounty":null,"asmTagIds":[],"assetTypes":[],"from":0,"size":100,"sort":{"field":"cvss_score","direction":"DESC"},"product_area":"h1_assets","product_feature":"policy_scopes"},"query":"query PolicySearchStructuredScopesQuery($handle: String!, $searchString: String, $eligibleForSubmission: Boolean, $eligibleForBounty: Boolean, $minSeverityScore: SeverityRatingEnum, $asmTagIds: [Int], $assetTypes: [StructuredScopeAssetTypeEnum!], $from: Int, $size: Int, $sort: SortInput) {\n  team(handle: $handle) {\n    id\n    team_display_options {\n      show_total_reports_per_asset\n      __typename\n    }\n    structured_scopes_search(\n      search_string: $searchString\n      eligible_for_submission: $eligibleForSubmission\n      eligible_for_bounty: $eligibleForBounty\n      min_severity_score: $minSeverityScore\n      asm_tag_ids: $asmTagIds\n      asset_types: $assetTypes\n      from: $from\n      size: $size\n      sort: $sort\n    ) {\n      nodes {\n        ... on StructuredScopeDocument {\n          id\n          ...PolicyScopeStructuredScopeDocument\n          __typename\n        }\n        __typename\n      }\n      pageInfo {\n        startCursor\n        hasPreviousPage\n        endCursor\n        hasNextPage\n        __typename\n      }\n      total_count\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment PolicyScopeStructuredScopeDocument on StructuredScopeDocument {\n  id\n  identifier\n  display_name\n  instruction\n  cvss_score\n  eligible_for_bounty\n  eligible_for_submission\n  asm_system_tags\n  created_at\n  updated_at\n  total_resolved_reports\n  attachments {\n    id\n    file_name\n    file_size\n    content_type\n    expiring_url\n    __typename\n  }\n  __typename\n}\n"}

example response:

response
{
    "data": {
        "team": {
            "id": "Z2lkOi8vaGFja2Vyb25lL0VuZ2FnZW1lbnRzOjpCdWdCb3VudHlQcm9ncmFtLzE5Mw==",
            "team_display_options": {
                "show_total_reports_per_asset": true,
                "__typename": "TeamDisplayOptions"
            },
            "structured_scopes_search": {
                "nodes": [
                    {
                        "id": "Z2lkOi8vaGFja2Vyb25lL1N0cnVjdHVyZWRTY29wZXNJbmRleC84NTg5MQ==",
                        "identifier": "com.bitso.alpha",
                        "display_name": "AndroidPlayStore",
                        "instruction": "",
                        "cvss_score": "critical",
                        "eligible_for_bounty": true,
                        "eligible_for_submission": true,
                        "asm_system_tags": [],
                        "created_at": "2021-10-29T15:28:19.986Z",
                        "updated_at": "2021-10-29T15:28:20.011Z",
                        "total_resolved_reports": 0,
                        "attachments": [],
                        "__typename": "StructuredScopeDocument"
                    },
                    {
                        "id": "Z2lkOi8vaGFja2Vyb25lL1N0cnVjdHVyZWRTY29wZXNJbmRleC84NTg5Mg==",
                        "identifier": "1539469172",
                        "display_name": "IosAppStore",
                        "instruction": "",
                        "cvss_score": "critical",
                        "eligible_for_bounty": true,
                        "eligible_for_submission": true,
                        "asm_system_tags": [],
                        "created_at": "2021-10-29T15:32:07.951Z",
                        "updated_at": "2021-10-29T15:32:07.975Z",
                        "total_resolved_reports": 0,
                        "attachments": [],
                        "__typename": "StructuredScopeDocument"
                    }
                ],
                "pageInfo": {
                    "startCursor": "MQ",
                    "hasPreviousPage": false,
                    "endCursor": "MzI",
                    "hasNextPage": false,
                    "__typename": "PageInfo"
                },
                "total_count": 32,
                "__typename": "SearchResultConnection"
            },
            "__typename": "Team"
        }
    }
}
what we need:
"identifier":"nvio.ar", # this is the scraped domain
"display_name":"Domain", # if Wildcards, put it in wildcards. if Domain or Url: put protocol in front (https) and put it in domains.txt. If else, skip it.

if "display_name":"Domain" or "display_name":"Url", put "identifier in domains.txt" 
if "display_name":"Wildcard", put it in wildcards.txt