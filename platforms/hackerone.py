import os
from datetime import datetime, timezone

from config.constants import DOMAINS_BASENAME, TARGETS_BASENAME, WILDCARDS_BASENAME
from platforms.base import AuthenticationError, BasePlatformClient
from utils.io import read_lines_resilient
from utils.models import ProgramRecord, QueryOptions


class HackerOneClient(BasePlatformClient):
    platform_label = "HackerOne"

    def _token(self) -> str | None:
        h1_creds = self.config.get("credentials", {}).get("h1", {})
        return h1_creds.get("token") or h1_creds.get("cookie")

    def _build_headers(self, token: str) -> dict:
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/json",
        }

        if token.lower().startswith("bearer "):
            headers["Authorization"] = token
        else:
            headers["Cookie"] = token

        return headers

    def request_json(self, url, headers, json_data=None):
        response = self.request(url, headers, method="POST" if json_data else "GET", json_data=json_data)

        if response.status_code >= 400:
            raise RuntimeError(f"H1 request failed with status {response.status_code}: {response.text[:200]}")

        return response.json()

    def fetch_opportunities_with_sort_direction(self, api_url, headers, sort_field, sort_direction="DESC"):
        print(f"Fetching opportunities sorted by {sort_field} in {sort_direction} order...")
        query = {
            "operationName": "DiscoveryQuery",
            "variables": {
                "from": 0,
                "size": 100,
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
                    launched_at
                    __typename
                  }
                  __typename
                }
                __typename
              }
            }
            """,
        }

        response = self.request_json(api_url, headers, query)

        if "data" in response and "opportunities_search" in response["data"]:
            print("Opportunities fetched successfully.")
            return response["data"]

        raise RuntimeError(f"Unexpected response format: {response}")

    def fetch_identifiers_for_handle(self, api_url, headers, handle):
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
                      identifier
                      display_name
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
                __typename
              }
            }
            """,
        }

        response = self.request_json(api_url, headers, query)

        if "data" in response and "team" in response["data"] and response["data"]["team"]:
            return response["data"]["team"].get("structured_scopes_search", {}).get("nodes", [])

        return []

    def fetch_opportunities_sort_desc(self, api_url, headers):
        return self.fetch_opportunities_with_sort_direction(api_url, headers, sort_field="launched_at", sort_direction="DESC")

    def remove_duplicates(self, file_path):
        lines = [line.strip() for line in read_lines_resilient(file_path)]
        unique_lines = sorted({line for line in lines if line})

        with open(file_path, "w", encoding="utf-8") as file:
            if unique_lines:
                file.write("\n".join(unique_lines) + "\n")

    def check_auth(self):
        token = self._token()
        if not token:
            print("H1 token is empty. Set H1_TOKEN in .env.")
            return False

        headers = self._build_headers(token)

        try:
            self.fetch_opportunities_sort_desc("https://hackerone.com/graphql", headers)
        except AuthenticationError as exc:
            print(str(exc))
            return False
        except RuntimeError as exc:
            print(str(exc))
            return False

        print("H1 auth preflight succeeded.")
        return True

    def run(self, targets_file, wildcards_file, domains_file, query_options: QueryOptions):
        print("Starting H1 script...")
        graphql_url = "https://hackerone.com/graphql"
        token = self._token()

        if not token:
            print("H1 token is empty. Set H1_TOKEN in .env.")
            return []

        for path in (targets_file, wildcards_file, domains_file):
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)

        headers = self._build_headers(token)

        try:
            opportunities_data_desc = self.fetch_opportunities_sort_desc(graphql_url, headers)
        except (AuthenticationError, RuntimeError) as exc:
            print(str(exc))
            return []

        opportunities = opportunities_data_desc.get("opportunities_search", {}).get("nodes", [])
        opportunities_filtered = []

        for opportunity in opportunities:
            handle = opportunity.get("handle")
            launched_at = parse_datetime(opportunity.get("launched_at"))
            if not handle:
                continue

            if query_options.mode == "new":
                if launched_at is None:
                    continue
                if query_options.cutoff and launched_at < query_options.cutoff:
                    continue

            opportunities_filtered.append({"handle": handle, "launched_at": launched_at})

        opportunities_filtered.sort(key=lambda x: x["launched_at"] or datetime.min, reverse=True)

        with open(targets_file, "w", encoding="utf-8") as file:
            handles = [item["handle"] for item in opportunities_filtered]
            if handles:
                file.write("\n".join(handles) + "\n")

        all_wildcards = []
        all_domains = []
        records: list[ProgramRecord] = []

        for item in opportunities_filtered:
            handle = item["handle"]
            launched_at = item["launched_at"]
            print(f"Fetching identifiers for handle: {handle}")

            try:
                identifiers = self.fetch_identifiers_for_handle(graphql_url, headers, handle)
            except (AuthenticationError, RuntimeError) as exc:
                print(str(exc))
                continue

            record = ProgramRecord(platform="hackerone", name=handle, launched_at=launched_at)

            for scope in identifiers:
                identifier = scope.get("identifier")
                display_name = scope.get("display_name")
                if not identifier:
                    continue

                if display_name in ("Domain", "Url"):
                    record.domains.append(identifier)
                    all_domains.append(identifier)
                elif display_name == "Wildcard":
                    record.wildcards.append(identifier)
                    all_wildcards.append(identifier)

            records.append(record)

        with open(wildcards_file, "w", encoding="utf-8") as file:
            if all_wildcards:
                file.write("\n".join(all_wildcards) + "\n")

        with open(domains_file, "w", encoding="utf-8") as file:
            if all_domains:
                file.write("\n".join(all_domains) + "\n")

        self.remove_duplicates(wildcards_file)
        self.remove_duplicates(domains_file)

        records.sort(key=lambda r: r.launched_at or datetime.min, reverse=True)
        return records


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    cleaned = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is not None:
            return parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    except ValueError:
        return None


def check_auth(config):
    return HackerOneClient(config).check_auth()


def main(
    config,
    targets_file=TARGETS_BASENAME,
    wildcards_file=WILDCARDS_BASENAME,
    domains_file=DOMAINS_BASENAME,
    query_options: QueryOptions | None = None,
):
    options = query_options or QueryOptions()
    return HackerOneClient(config).run(targets_file, wildcards_file, domains_file, options)
