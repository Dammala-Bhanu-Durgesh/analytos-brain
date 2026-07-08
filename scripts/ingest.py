from __future__ import annotations

import argparse
import copy
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brain.extract import ingest_markdown
from brain.graph import diff_graph
from brain.storage import load_branch, save_branch, set_latest_branch


def run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest seed markdown into a governed branch.")
    parser.add_argument("--source", default="seed-data", help="Folder containing markdown seed files.")
    parser.add_argument("--branch", default=None, help="Branch name. Defaults to ingest/<timestamp>.")
    args = parser.parse_args()

    source = ROOT / args.source
    if not source.exists():
        raise SystemExit(f"Missing source folder: {source}")
    branch = args.branch or f"ingest/{run_id()}"
    graph = copy.deepcopy(load_branch("main"))
    for path in sorted(source.glob("*.md")):
        ingest_markdown(graph, path)
    save_branch(branch, graph)
    set_latest_branch(branch)
    diff = diff_graph(load_branch("main"), graph)
    print(f"Created branch {branch}")
    print(diff["summary"])


if __name__ == "__main__":
    main()

