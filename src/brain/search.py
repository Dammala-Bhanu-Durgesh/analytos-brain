from __future__ import annotations

import re
from typing import Any

from .policy import filter_nodes
from .storage import commits, load_branch


def node_text(node: dict[str, Any]) -> str:
    values = [node["id"], node["type"]]
    values.extend(str(v) for v in node.get("properties", {}).values())
    return " ".join(values).lower()


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def search(actor: str, query: str, branch: str = "main", limit: int = 10) -> list[dict[str, Any]]:
    graph = load_branch(branch)
    q_tokens = tokenize(query)
    results = []
    for node in filter_nodes(actor, list(graph["nodes"].values())):
        text = node_text(node)
        tokens = tokenize(text)
        overlap = len(q_tokens & tokens)
        substring_boost = 2 if query.lower() in text else 0
        score = overlap + substring_boost
        if score:
            item = dict(node)
            item["score"] = score
            results.append(item)
    return sorted(results, key=lambda n: (-n["score"], n["type"], n["id"]))[:limit]


def entities(actor: str, branch: str = "main") -> dict[str, list[dict[str, Any]]]:
    graph = load_branch(branch)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for node in filter_nodes(actor, list(graph["nodes"].values())):
        grouped.setdefault(node["type"], []).append(node)
    return {kind: sorted(items, key=lambda n: n["id"]) for kind, items in sorted(grouped.items())}


def recent_changes(limit: int = 20) -> list[dict[str, Any]]:
    return commits()[:limit]

