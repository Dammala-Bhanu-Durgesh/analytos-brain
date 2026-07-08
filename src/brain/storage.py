from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import GraphDict, empty_graph

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / ".analytos-brain"
BRANCH_DIR = STATE_DIR / "branches"
COMMITS_FILE = STATE_DIR / "commits.json"
LATEST_BRANCH_FILE = STATE_DIR / "latest_branch.txt"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_state() -> None:
    BRANCH_DIR.mkdir(parents=True, exist_ok=True)
    if not (BRANCH_DIR / "main.json").exists():
        save_branch("main", empty_graph())
    if not COMMITS_FILE.exists():
        write_json(COMMITS_FILE, [])


def branch_path(branch: str) -> Path:
    return BRANCH_DIR / f"{branch.replace('/', '__')}.json"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return copy.deepcopy(default)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_branch(branch: str) -> GraphDict:
    ensure_state()
    return read_json(branch_path(branch), empty_graph())


def save_branch(branch: str, graph: GraphDict) -> None:
    ensure_state() if branch != "main" else BRANCH_DIR.mkdir(parents=True, exist_ok=True)
    write_json(branch_path(branch), graph)


def list_branches() -> list[str]:
    ensure_state()
    return sorted(p.stem.replace("__", "/") for p in BRANCH_DIR.glob("*.json"))


def delete_branch(branch: str) -> None:
    path = branch_path(branch)
    if branch == "main":
        raise ValueError("main cannot be deleted")
    if path.exists():
        path.unlink()


def latest_branch() -> str | None:
    if not LATEST_BRANCH_FILE.exists():
        return None
    value = LATEST_BRANCH_FILE.read_text(encoding="utf-8").strip()
    return value or None


def set_latest_branch(branch: str) -> None:
    LATEST_BRANCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    LATEST_BRANCH_FILE.write_text(branch, encoding="utf-8")


def commits() -> list[dict[str, Any]]:
    ensure_state()
    return read_json(COMMITS_FILE, [])


def append_commit(commit: dict[str, Any]) -> None:
    items = commits()
    items.insert(0, commit)
    write_json(COMMITS_FILE, items)

