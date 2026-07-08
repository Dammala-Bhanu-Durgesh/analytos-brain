from __future__ import annotations

import copy
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brain.extract import ingest_markdown
from brain.graph import diff_graph, merge_branch
from brain.policy import can_read
from brain.search import entities, search
from brain.storage import STATE_DIR, ensure_state, load_branch, save_branch


def reset() -> None:
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)
    ensure_state()


def ingest_all(branch: str) -> None:
    graph = copy.deepcopy(load_branch("main"))
    for path in sorted((ROOT / "seed-data").glob("*.md")):
        ingest_markdown(graph, path)
    save_branch(branch, graph)


def test_ingest_does_not_write_main_until_approved() -> None:
    reset()
    ingest_all("ingest/test")
    assert load_branch("main")["nodes"] == {}
    diff = diff_graph(load_branch("main"), load_branch("ingest/test"))
    assert diff["summary"]["added_nodes"] > 0


def test_reingest_same_docs_is_idempotent() -> None:
    reset()
    ingest_all("ingest/one")
    first = load_branch("ingest/one")
    save_branch("main", first)
    ingest_all("ingest/two")
    diff = diff_graph(load_branch("main"), load_branch("ingest/two"))
    assert diff["summary"] == {
        "added_nodes": 0,
        "changed_nodes": 0,
        "added_edges": 0,
        "changed_edges": 0,
    }


def test_merge_records_actor_and_enables_search() -> None:
    reset()
    ingest_all("ingest/test")
    commit = merge_branch("ingest/test", "reviewer@santosh")
    assert commit["actor"] == "reviewer@santosh"
    assert search("content-agent", "phantom inventory")


def test_content_agent_cannot_read_internal_email_threads() -> None:
    reset()
    ingest_all("ingest/test")
    merge_branch("ingest/test", "reviewer@santosh")
    reviewer_entities = entities("reviewer")
    email_threads = reviewer_entities["EmailThread"]
    assert email_threads
    assert not any(can_read("content-agent", node) for node in email_threads)
    assert not any(node["type"] == "EmailThread" for node in search("content-agent", "Stockly pilot email"))


if __name__ == "__main__":
    tests = [
        test_ingest_does_not_write_main_until_approved,
        test_reingest_same_docs_is_idempotent,
        test_merge_records_actor_and_enables_search,
        test_content_agent_cannot_read_internal_email_threads,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")

