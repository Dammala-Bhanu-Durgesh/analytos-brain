from __future__ import annotations

from typing import Any

ROLE_RULES = {
    "content-agent": {
        "read_types": {"Product", "Feature", "ProofPoint", "Persona", "ICPSegment", "Decision"},
        "public_only": True,
    },
    "gtm-agent": {
        "read_types": {"Product", "Feature", "ProofPoint", "Persona", "ICPSegment"},
        "public_only": True,
    },
    "dashboard": {
        "read_types": {"Product", "Feature", "ProofPoint", "Persona", "ICPSegment", "Decision"},
        "public_only": True,
    },
    "reviewer": {
        "read_types": {
            "Product",
            "Feature",
            "ProofPoint",
            "Persona",
            "ICPSegment",
            "Person",
            "EmailThread",
            "Decision",
        },
        "public_only": False,
    },
}


def can_read(actor: str, node: dict[str, Any]) -> bool:
    rule = ROLE_RULES.get(actor, ROLE_RULES["dashboard"])
    visibility = node.get("properties", {}).get("visibility", "public")
    if node["type"] not in rule["read_types"]:
        return False
    if rule["public_only"] and visibility != "public":
        return False
    return True


def filter_nodes(actor: str, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [node for node in nodes if can_read(actor, node)]

