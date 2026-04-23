#!/usr/bin/env python3
"""Fetch PR review data from GitHub for offline analysis."""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

# === Configuration ===
REPOS = ["rpm-software-management/dnf5"]
PR_LIMIT = 200  # Total PRs to fetch (script will paginate as needed)
PR_LIST_PAGE_SIZE = 50  # PRs per GraphQL page (max ~50 to avoid API errors)
GRAPHQL_BATCH_SIZE = 10  # Reviews fetched per GraphQL query
BATCH_SLEEP = 0.5  # seconds between GraphQL batches
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


class GitHubAPIError(Exception):
    """Exception raised when GitHub API returns an error."""
    pass


def run_gh(args: list[str], check: bool = True) -> str:
    """Run a gh CLI command and return stdout. Raises GitHubAPIError on non-zero exit if check=True."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        error_msg = f"Error running gh {' '.join(args)}\n{result.stderr}"
        raise GitHubAPIError(error_msg)
    return result.stdout


def load_existing_data(output_file: str) -> dict:
    """Load existing PR data if the file exists."""
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing data from {output_file}: {e}", file=sys.stderr)
    return {"pull_requests": []}


def fetch_pr_list_graphql(owner: str, name: str, limit: int, skip_numbers: set[int]) -> list[dict]:
    """Fetch PR metadata using GraphQL with pagination support."""
    print(f"[{owner}/{name}] Fetching merged PRs via GraphQL...", file=sys.stderr)

    all_prs = []
    cursor = None
    has_next_page = True

    while has_next_page and len(all_prs) < limit:
        # Build paginated query
        after_clause = f', after: "{cursor}"' if cursor else ''
        query = f'''
        {{
          repository(owner: "{owner}", name: "{name}") {{
            pullRequests(first: {PR_LIST_PAGE_SIZE}, states: MERGED, orderBy: {{field: CREATED_AT, direction: DESC}}{after_clause}) {{
              pageInfo {{
                hasNextPage
                endCursor
              }}
              nodes {{
                number
                title
                body
                author {{ login }}
                changedFiles
                additions
                deletions
                labels(first: 20) {{ nodes {{ name }} }}
                reviewDecision
                createdAt
                mergedAt
                url
                comments(first: 50) {{
                  nodes {{
                    author {{ login }}
                    body
                    createdAt
                    url
                  }}
                }}
              }}
            }}
          }}
        }}
        '''

        # Fetch page
        max_retries = 3
        for attempt in range(max_retries):
            try:
                stdout = run_gh(["api", "graphql", "-f", f"query={query}"], check=False)
                response = json.loads(stdout)

                if "errors" in response:
                    raise GitHubAPIError(f"GraphQL errors: {response['errors']}")

                data = response.get("data", {}).get("repository", {}).get("pullRequests", {})
                page_info = data.get("pageInfo", {})
                nodes = data.get("nodes", [])

                # Filter out PRs we already have
                new_prs = [pr for pr in nodes if pr["number"] not in skip_numbers]
                all_prs.extend(new_prs)

                if new_prs:
                    print(f"[{owner}/{name}] Fetched {len(all_prs)}/{limit} PRs (added {len(new_prs)} new from this page)...", file=sys.stderr)
                else:
                    print(f"[{owner}/{name}] Page had no new PRs (all {len(nodes)} already fetched)", file=sys.stderr)

                # Update pagination
                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")

                if not has_next_page:
                    print(f"[{owner}/{name}] Reached end of PRs", file=sys.stderr)

                break  # Success

            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"[{owner}/{name}] Error fetching PRs (attempt {attempt + 1}/{max_retries}): {e}", file=sys.stderr)
                    print(f"[{owner}/{name}] Retrying in {wait_time}s...", file=sys.stderr)
                    time.sleep(wait_time)
                else:
                    raise

        # Small delay between pages
        if has_next_page and len(all_prs) < limit:
            time.sleep(0.3)

    print(f"[{owner}/{name}] Got {len(all_prs)} new PRs", file=sys.stderr)
    return all_prs[:limit]  # Trim to limit


def normalize_pr_from_graphql(pr_data: dict) -> dict:
    """Normalize a PR from GraphQL format to our storage format (without reviews)."""
    return {
        "number": pr_data["number"],
        "title": pr_data["title"],
        "url": pr_data["url"],
        "author": pr_data["author"]["login"] if pr_data.get("author") else None,
        "body": pr_data.get("body", ""),
        "labels": [l["name"] for l in pr_data.get("labels", {}).get("nodes", [])],
        "reviewDecision": pr_data.get("reviewDecision", ""),
        "createdAt": pr_data["createdAt"],
        "mergedAt": pr_data.get("mergedAt", ""),
        "changedFiles": pr_data.get("changedFiles", 0),
        "additions": pr_data.get("additions", 0),
        "deletions": pr_data.get("deletions", 0),
        "comments": [
            {
                "author": c["author"]["login"] if c.get("author") else None,
                "body": c["body"],
                "createdAt": c["createdAt"],
                "url": c.get("url", ""),
            }
            for c in pr_data.get("comments", {}).get("nodes", [])
        ],
        "reviews": [],  # Will be filled by fetch_all_reviews
    }


def build_graphql_query(owner: str, name: str, pr_numbers: list[int]) -> str:
    """Build a batched GraphQL query for review data."""
    fragments = []
    for n in pr_numbers:
        fragments.append(f"""
    pr_{n}: pullRequest(number: {n}) {{
      number
      reviews(first: 100) {{
        nodes {{
          author {{ login }}
          state
          body
          comments(first: 100) {{
            nodes {{
              body
              path
              line
              author {{ login }}
            }}
          }}
        }}
      }}
    }}""")

    query = '{\n  repository(owner: "' + owner + '", name: "' + name + '") {' + ''.join(fragments) + '\n  }\n}'
    return query


def fetch_reviews_batch(owner: str, name: str, pr_numbers: list[int]) -> dict[int, list]:
    """Fetch review data for a batch of PRs via GraphQL. Returns {pr_number: reviews_list}."""
    query = build_graphql_query(owner, name, pr_numbers)

    # GraphQL calls may exit non-zero with partial errors, so don't check exit code
    stdout = run_gh(["api", "graphql", "-f", f"query={query}"], check=False)

    try:
        response = json.loads(stdout)
    except json.JSONDecodeError as e:
        print(f"Error parsing GraphQL response: {e}", file=sys.stderr)
        print(f"Response: {stdout[:500]}", file=sys.stderr)
        return {}

    if "errors" in response:
        print(f"GraphQL errors: {response['errors']}", file=sys.stderr)

    result = {}
    repo_data = response.get("data", {}).get("repository", {})

    for n in pr_numbers:
        alias = f"pr_{n}"
        pr_data = repo_data.get(alias)

        if pr_data is None:
            print(f"Warning: PR {n} not found in GraphQL response", file=sys.stderr)
            result[n] = []
        else:
            result[n] = pr_data.get("reviews", {}).get("nodes", [])

    return result


def fetch_all_reviews(owner: str, name: str, pr_numbers: list[int]) -> dict[int, list]:
    """Fetch reviews for all PRs, batched. Returns {pr_number: reviews_list}."""
    all_reviews = {}
    total_batches = (len(pr_numbers) + GRAPHQL_BATCH_SIZE - 1) // GRAPHQL_BATCH_SIZE

    for i in range(0, len(pr_numbers), GRAPHQL_BATCH_SIZE):
        batch = pr_numbers[i:i + GRAPHQL_BATCH_SIZE]
        batch_num = (i // GRAPHQL_BATCH_SIZE) + 1

        print(f"[{owner}/{name}] Reviews: batch {batch_num}/{total_batches} (PRs {batch[0]}-{batch[-1]})", file=sys.stderr)

        batch_reviews = fetch_reviews_batch(owner, name, batch)
        all_reviews.update(batch_reviews)

        if i + GRAPHQL_BATCH_SIZE < len(pr_numbers) and BATCH_SLEEP > 0:
            time.sleep(BATCH_SLEEP)

    return all_reviews


def process_repo(repo: str) -> None:
    """Full pipeline for one repo: list PRs, fetch reviews, write JSON."""
    owner, name = repo.split("/")
    output_file = os.path.join(OUTPUT_DIR, f"{owner}__{name}.json")

    # Phase 0: Load existing data
    existing_data = load_existing_data(output_file)
    existing_prs = {pr["number"]: pr for pr in existing_data.get("pull_requests", [])}

    if existing_prs:
        print(f"[{repo}] Found {len(existing_prs)} existing PRs", file=sys.stderr)

    # Phase 1: Fetch new PRs using GraphQL with pagination
    new_prs_data = fetch_pr_list_graphql(owner, name, PR_LIMIT - len(existing_prs), set(existing_prs.keys()))

    if not new_prs_data and not existing_prs:
        print(f"[{repo}] No PRs found", file=sys.stderr)
        return

    # Phase 2: Fetch reviews for new PRs only
    if new_prs_data:
        new_pr_numbers = [pr["number"] for pr in new_prs_data]
        print(f"[{repo}] Fetching reviews for {len(new_pr_numbers)} new PRs...", file=sys.stderr)
        new_reviews = fetch_all_reviews(owner, name, new_pr_numbers)

        # Normalize new PRs and add reviews
        for pr_data in new_prs_data:
            pr_num = pr_data["number"]
            normalized = normalize_pr_from_graphql(pr_data)
            reviews = new_reviews.get(pr_num, [])
            normalized["reviews"] = [
                {
                    "author": r["author"]["login"] if r.get("author") else None,
                    "state": r["state"],
                    "body": r.get("body", ""),
                    "inline_comments": [
                        {
                            "author": ic["author"]["login"] if ic.get("author") else None,
                            "body": ic["body"],
                            "path": ic["path"],
                            "line": ic["line"],
                        }
                        for ic in r.get("comments", {}).get("nodes", [])
                    ],
                }
                for r in reviews
            ]
            existing_prs[pr_num] = normalized
    else:
        print(f"[{repo}] No new PRs to fetch", file=sys.stderr)

    # Phase 3: Merge and sort by number (descending)
    all_prs = sorted(existing_prs.values(), key=lambda x: x["number"], reverse=True)

    # Keep only PR_LIMIT most recent PRs
    all_prs = all_prs[:PR_LIMIT]

    # Write output
    output = {
        "repo": repo,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "pull_requests": all_prs,
    }

    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[{repo}] Wrote {output_file} ({len(all_prs)} total PRs, {len(new_prs_data) if new_prs_data else 0} newly fetched)", file=sys.stderr)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for repo in REPOS:
        try:
            process_repo(repo)
        except Exception as e:
            print(f"[{repo}] Error: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            continue


if __name__ == "__main__":
    main()
