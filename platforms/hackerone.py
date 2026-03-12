import requests

from utils.io import read_lines_resilient


class AuthenticationError(RuntimeError):
    pass


def make_request(url, headers, json_data=None):
    """Make a request to the specified URL with optional JSON data."""
    try:
        if json_data:
            response = requests.post(url, headers=headers, json=json_data, timeout=30)
        else:
            response = requests.get(url, headers=headers, timeout=30)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Error making request to {url}: {exc}") from exc

    if response.status_code in (401, 403):
        raise AuthenticationError(
            f"HackerOne authentication failed with status {response.status_code}. Refresh your H1 credential."
        )

    if response.status_code >= 400:
        raise RuntimeError(f"H1 request failed with status {response.status_code}: {response.text[:200]}")

    return response.json()


def fetch_opportunities_with_sort_direction(api_url, headers, sort_field, sort_direction="DESC"):
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
                                "must_not": {"term": {"team_type": "Engagements::Assessment"}},
                                "should": [{"term": {"offers_bounties": True}}],
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {"exists": {"field": "structured_scope_stats.URL"}},
                                    {"exists": {"field": "structured_scope_stats.WILDCARD"}},
                                    {"exists": {"field": "structured_scope_stats.API"}},
                                ]
                            }
                        },
                        {"range": {"minimum_low": {"gte": 1}}},
                    ]
                }
            },
            "sort": [{"field": sort_field, "direction": sort_direction}],
            "post_filters": {
                "my_programs": False,
                "bookmarked": False,
                "campaign_teams": False,
            },
            "product_area": "opportunity_discovery",
            "product_feature": "search",
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
        """,
    }

    response = make_request(api_url, headers, query)

    if "data" in response and "opportunities_search" in response["data"]:
        print("Opportunities fetched successfully.")
        return response["data"]

    raise RuntimeError(f"Unexpected response format: {response}")


def fetch_identifiers_for_handle(api_url, headers, handle):
    print(f"Fetching identifiers for handle: {handle}")

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
            "product_feature": "policy_scopes",
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
                ... on StructuredScopeDocument {
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
        """,
    }

    response = make_request(api_url, headers, query)

    if "data" in response and "team" in response["data"] and response["data"]["team"]:
        return response["data"]["team"].get("structured_scopes_search", {}).get("nodes", [])

    print(f"Unexpected response format for handle {handle}: {response}")
    return []


def collect_identifiers_from_targets(api_url, headers, targets_file="targets.txt", wildcards_file="wildcards.txt", domains_file="domains.txt"):
    handles = [line.strip() for line in read_lines_resilient(targets_file) if line.strip()]

    wildcards = []
    domains = []

    for handle in handles:
        identifiers = fetch_identifiers_for_handle(api_url, headers, handle)
        for item in identifiers:
            identifier = item.get("identifier")
            display_name = item.get("display_name")
            if not identifier:
                continue

            if display_name in ("Domain", "Url"):
                domains.append(identifier)
            elif display_name == "Wildcard":
                wildcards.append(identifier)

    with open(wildcards_file, "w", encoding="utf-8") as file:
        if wildcards:
            file.write("\n".join(wildcards) + "\n")
    print(f"Wildcards saved to {wildcards_file} ({len(wildcards)} collected)")

    with open(domains_file, "w", encoding="utf-8") as file:
        if domains:
            file.write("\n".join(domains) + "\n")
    print(f"Domains saved to {domains_file} ({len(domains)} collected)")


def fetch_opportunities_sort_desc(api_url, headers):
    return fetch_opportunities_with_sort_direction(api_url, headers, sort_field="launched_at", sort_direction="DESC")


def remove_duplicates(file_path):
    print(f"Removing duplicate lines from {file_path}...")
    lines = [line.strip() for line in read_lines_resilient(file_path)]
    unique_lines = sorted({line for line in lines if line})

    with open(file_path, "w", encoding="utf-8") as file:
        if unique_lines:
            file.write("\n".join(unique_lines) + "\n")
    print(f"Removed duplicates, {len(lines) - len(unique_lines)} duplicates found.")


def check_auth(config):
    try:
        credential = config["credentials"]["h1"]["cookie"]
    except KeyError:
        print("H1 credential missing: credentials.h1.cookie")
        return False

    if not credential:
        print("H1 credential is empty. Set H1_COOKIE in .env.")
        return False

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
    }

    if credential.lower().startswith("bearer "):
        headers["Authorization"] = credential
    else:
        headers["Cookie"] = credential

    try:
        fetch_opportunities_sort_desc("https://hackerone.com/graphql", headers)
    except AuthenticationError as exc:
        print(str(exc))
        return False
    except RuntimeError as exc:
        print(str(exc))
        return False

    print("H1 auth preflight succeeded.")
    return True


def main(config, targets_file="targets.txt", wildcards_file="wildcards.txt", domains_file="domains.txt"):
    print("Starting H1 script...")
    graphql_url = "https://hackerone.com/graphql"

    try:
        credential = config["credentials"]["h1"]["cookie"]
    except KeyError as exc:
        print(f"Missing key in config: {exc}")
        return

    if not credential:
        print("H1 credential is empty. Set H1_COOKIE in .env.")
        return

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
    }

    if credential.lower().startswith("bearer "):
        headers["Authorization"] = credential
    else:
        headers["Cookie"] = credential

    try:
        opportunities_data_desc = fetch_opportunities_sort_desc(graphql_url, headers)
    except (AuthenticationError, RuntimeError) as exc:
        print(str(exc))
        return

    handles_desc = []
    for opportunity in opportunities_data_desc.get("opportunities_search", {}).get("nodes", []):
        handle = opportunity.get("handle")
        if handle:
            handles_desc.append(handle)

    with open(targets_file, "w", encoding="utf-8") as file:
        if handles_desc:
            file.write("\n".join(handles_desc) + "\n")

    try:
        collect_identifiers_from_targets(
            graphql_url,
            headers,
            targets_file=targets_file,
            wildcards_file=wildcards_file,
            domains_file=domains_file,
        )
    except (AuthenticationError, RuntimeError) as exc:
        print(str(exc))
        return

    remove_duplicates(wildcards_file)
    remove_duplicates(domains_file)
