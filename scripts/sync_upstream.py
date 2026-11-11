#!/usr/bin/env python3
"""Compare and sync vendored upstream/hm3-cpl against toastygm/hm3-cpl."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_REMOTE_NAME = "upstream-hm3-cpl"
DEFAULT_REMOTE_URL = "https://github.com/toastygm/hm3-cpl.git"
DEFAULT_REMOTE_BRANCH = "main"
SUBTREE_PREFIX = "upstream/hm3-cpl"


def run_git(
    repo_root: Path,
    args: list[str],
    *,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Execute a git command in repo_root and return the CompletedProcess."""
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=check,
    )


def ensure_remote(repo_root: Path, remote_name: str, remote_url: str) -> None:
    """Ensure the upstream git remote exists, points to remote_url, and skips tags."""
    existing = run_git(repo_root, ["remote", "get-url", remote_name], check=False)
    if existing.returncode != 0:
        run_git(repo_root, ["remote", "add", remote_name, remote_url])
        print(f"Added git remote {remote_name!r} -> {remote_url}")
    elif existing.stdout.strip() != remote_url:
        run_git(repo_root, ["remote", "set-url", remote_name, remote_url])
        print(f"Updated git remote {remote_name!r} -> {remote_url}")

    run_git(repo_root, ["config", f"remote.{remote_name}.tagOpt", "--no-tags"])


def read_manifest_version(repo_root: Path, tree_ref: str) -> str:
    """Read module.json version from a git treeish (e.g. 'HEAD:upstream/hm3-cpl')."""
    sep = "/" if ":" in tree_ref else ":"
    res = run_git(repo_root, ["show", f"{tree_ref}{sep}module.json"], check=False)
    if res.returncode != 0:
        return "unknown"
    try:
        return str(json.loads(res.stdout).get("version", "unknown"))
    except json.JSONDecodeError:
        return "unknown"


def get_short_sha(repo_root: Path, rev: str) -> str:
    """Return short commit hash for rev, or 'unknown' if missing."""
    res = run_git(repo_root, ["rev-parse", "--short", rev], check=False)
    return res.stdout.strip() if res.returncode == 0 else "unknown"


def get_merge_base(repo_root: Path, remote_ref: str) -> str | None:
    """Return the latest upstream commit merged into HEAD, if any."""
    res = run_git(repo_root, ["merge-base", "HEAD", remote_ref], check=False)
    if res.returncode != 0:
        return None
    sha = res.stdout.strip()
    return sha or None


def compare_upstream(
    repo_root: Path,
    remote_ref: str,
    *,
    show_diff: bool,
    filter_paths: list[str],
) -> bool:
    """Print comparison between local HEAD:upstream/hm3-cpl and remote_ref.

    Returns True if upstream has file or commit differences, False if identical.
    """
    local_tree = f"HEAD:{SUBTREE_PREFIX}"
    local_ver = read_manifest_version(repo_root, local_tree)
    remote_ver = read_manifest_version(repo_root, remote_ref)
    remote_sha = get_short_sha(repo_root, remote_ref)
    merge_base = get_merge_base(repo_root, remote_ref)
    base_sha = merge_base[:7] if merge_base else "unknown"

    print(f"Local vendored ({SUBTREE_PREFIX}): v{local_ver} (upstream base {base_sha})")
    print(f"Upstream source ({remote_ref}):      v{remote_ver} (commit {remote_sha})")

    new_commits = ""
    if merge_base:
        log_res = run_git(
            repo_root,
            ["log", "--oneline", f"{merge_base}..{remote_ref}"],
            check=False,
        )
        new_commits = log_res.stdout.strip()

    stat_args = ["diff", "--stat", local_tree, remote_ref]
    if filter_paths:
        stat_args.extend(["--", *filter_paths])
    stat_res = run_git(repo_root, stat_args)
    diff_stat = stat_res.stdout.strip()

    if not new_commits and not diff_stat:
        print("Status: up to date (no changes).")
        return False

    if new_commits:
        print("\nNew upstream commits:")
        print(new_commits)

    if diff_stat:
        print("\nFile differences (local vs upstream):")
        print(diff_stat)
    else:
        print("\nFile differences: none in tracked file contents.")

    if show_diff and diff_stat:
        diff_args = ["diff", local_tree, remote_ref]
        if filter_paths:
            diff_args.extend(["--", *filter_paths])
        diff_res = run_git(repo_root, diff_args)
        print("\nFull diff:")
        print(diff_res.stdout, end="")

    return True


def pull_upstream(repo_root: Path, remote_name: str, branch: str) -> int:
    """Pull upstream changes into upstream/hm3-cpl via git subtree pull."""
    status_res = run_git(repo_root, ["status", "--porcelain"])
    if status_res.stdout.strip():
        print(
            "Error: working tree has uncommitted changes. "
            "Commit or stash them before running --pull.",
            file=sys.stderr,
        )
        return 1

    print(f"Pulling {remote_name}/{branch} into {SUBTREE_PREFIX}...")
    proc = subprocess.run(
        ["git", "subtree", "pull", f"--prefix={SUBTREE_PREFIX}", remote_name, branch],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return proc.returncode

    print("\nSubtree updated. Run `python scripts/build_mod.py` to rebuild the .mod file.")
    return 0


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--remote",
        default=DEFAULT_REMOTE_NAME,
        help=f"Git remote name for upstream (default: {DEFAULT_REMOTE_NAME})",
    )
    parser.add_argument(
        "--remote-url",
        default=DEFAULT_REMOTE_URL,
        help=f"Upstream repository URL (default: {DEFAULT_REMOTE_URL})",
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_REMOTE_BRANCH,
        help=f"Upstream branch to compare/pull (default: {DEFAULT_REMOTE_BRANCH})",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="Skip fetching from upstream and compare against cached remote tracking branch",
    )
    parser.add_argument(
        "--diff",
        action="store_true",
        help="Show full unified diff in addition to commit log and diffstat",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        dest="filter_paths",
        help="Optional path inside upstream/hm3-cpl to filter diffs (repeatable)",
    )
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Merge upstream changes into upstream/hm3-cpl via git subtree pull",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when upstream has changes (check mode only)",
    )
    args = parser.parse_args()

    ensure_remote(repo_root, args.remote, args.remote_url)

    if not args.no_fetch:
        fetch_res = run_git(repo_root, ["fetch", "--no-tags", args.remote, args.branch], check=False)
        if fetch_res.returncode != 0:
            print(
                f"Warning: failed to fetch from {args.remote_url}.\n"
                f"Local vendored copy in {SUBTREE_PREFIX}/ remains intact.\n"
                f"Git output: {fetch_res.stderr.strip()}",
                file=sys.stderr,
            )
            return 2

    remote_ref = f"{args.remote}/{args.branch}"
    has_changes = compare_upstream(
        repo_root,
        remote_ref,
        show_diff=args.diff,
        filter_paths=args.filter_paths,
    )

    if args.pull:
        if not has_changes:
            return 0
        return pull_upstream(repo_root, args.remote, args.branch)

    if args.exit_code and has_changes:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
