from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brain.graph import diff_graph, merge_branch, reject_branch
from brain.storage import latest_branch, list_branches, load_branch


def resolve_branch(value: str) -> str:
    if value == "ingest/latest":
        branch = latest_branch()
        if not branch:
            raise SystemExit("No latest ingest branch found.")
        return branch
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description="Review, approve, or reject ingestion branches.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    diff_cmd = sub.add_parser("diff")
    diff_cmd.add_argument("--branch", default="ingest/latest")
    approve = sub.add_parser("approve")
    approve.add_argument("--branch", default="ingest/latest")
    approve.add_argument("--actor", required=True)
    reject = sub.add_parser("reject")
    reject.add_argument("--branch", default="ingest/latest")
    reject.add_argument("--actor", required=True)
    args = parser.parse_args()

    if args.command == "list":
        print(json.dumps(list_branches(), indent=2))
    elif args.command == "diff":
        branch = resolve_branch(args.branch)
        print(json.dumps(diff_graph(load_branch("main"), load_branch(branch)), indent=2))
    elif args.command == "approve":
        branch = resolve_branch(args.branch)
        print(json.dumps(merge_branch(branch, args.actor), indent=2))
    elif args.command == "reject":
        branch = resolve_branch(args.branch)
        print(json.dumps(reject_branch(branch, args.actor), indent=2))


if __name__ == "__main__":
    main()

