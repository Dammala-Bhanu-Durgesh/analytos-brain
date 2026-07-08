from __future__ import annotations

import hashlib
from typing import Any

from .models import Edge, GraphDict, Node
from .storage import append_commit, delete_branch, load_branch, now_iso, save_branch


def stable_id(kind: str, *parts: str) -> str:
    raw = "|".join([kind, *[p.strip().lower() for p in parts if p]])
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    readable = "-".join(p.strip().lower().replace(" ", "-") for p in parts[:1] if p)
    return f"{kind.lower()}:{readable}-{digest}" if readable else f"{kind.lower()}:{digest}"


def edge_id(kind: str, from_id: str, to_id: str) -> str:
    return stable_id(kind, from_id, to_id)


def upsert_node(graph: GraphDict, node: Node) -> None:
    current = graph["nodes"].get(node.id)
    if current:
        merged = dict(current["properties"])
        merged.update({k: v for k, v in node.properties.items() if v not in (None, "", [])})
        current["properties"] = merged
        current["sources"] = sorted(set(current.get("sources", [])) | set(node.sources))
    else:
        graph["nodes"][node.id] = node.as_dict()


def upsert_edge(graph: GraphDict, edge: Edge) -> None:
    current = graph["edges"].get(edge.id)
    if current:
        current["sources"] = sorted(set(current.get("sources", [])) | set(edge.sources))
        current["properties"].update(edge.properties)
    else:
        graph["edges"][edge.id] = edge.as_dict()


def diff_graph(base: GraphDict, candidate: GraphDict) -> dict[str, Any]:
    added_nodes = []
    changed_nodes = []
    for node_id, node in candidate["nodes"].items():
        if node_id not in base["nodes"]:
            added_nodes.append(node)
        elif node != base["nodes"][node_id]:
            changed_nodes.append({"before": base["nodes"][node_id], "after": node})

    added_edges = []
    changed_edges = []
    for edge_key, edge in candidate["edges"].items():
        if edge_key not in base["edges"]:
            added_edges.append(edge)
        elif edge != base["edges"][edge_key]:
            changed_edges.append({"before": base["edges"][edge_key], "after": edge})

    return {
        "added_nodes": added_nodes,
        "changed_nodes": changed_nodes,
        "added_edges": added_edges,
        "changed_edges": changed_edges,
        "summary": {
            "added_nodes": len(added_nodes),
            "changed_nodes": len(changed_nodes),
            "added_edges": len(added_edges),
            "changed_edges": len(changed_edges),
        },
    }


def merge_branch(branch: str, actor: str) -> dict[str, Any]:
    if branch == "main":
        raise ValueError("main cannot be merged into itself")
    main = load_branch("main")
    candidate = load_branch(branch)
    diff = diff_graph(main, candidate)
    save_branch("main", candidate)
    commit = {
        "id": stable_id("commit", branch, actor, now_iso()),
        "branch": branch,
        "actor": actor,
        "approved_by": actor,
        "timestamp": now_iso(),
        "summary": diff["summary"],
        "source_documents": sorted(
            {
                source
                for node in candidate["nodes"].values()
                for source in node.get("sources", [])
            }
        ),
    }
    append_commit(commit)
    return commit


def reject_branch(branch: str, actor: str) -> dict[str, Any]:
    delete_branch(branch)
    commit = {
        "id": stable_id("reject", branch, actor, now_iso()),
        "branch": branch,
        "actor": actor,
        "approved_by": None,
        "timestamp": now_iso(),
        "summary": {"rejected": True},
        "source_documents": [],
    }
    append_commit(commit)
    return commit

