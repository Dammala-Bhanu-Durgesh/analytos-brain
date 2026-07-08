from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


GraphDict = dict[str, Any]


@dataclass
class Node:
    id: str
    type: str
    properties: dict[str, Any]
    sources: list[str] = field(default_factory=list)

    def as_dict(self) -> GraphDict:
        return {
            "id": self.id,
            "type": self.type,
            "properties": self.properties,
            "sources": sorted(set(self.sources)),
        }


@dataclass(frozen=True)
class Edge:
    id: str
    type: str
    from_id: str
    to_id: str
    properties: dict[str, Any]
    sources: tuple[str, ...]

    def as_dict(self) -> GraphDict:
        return {
            "id": self.id,
            "type": self.type,
            "from": self.from_id,
            "to": self.to_id,
            "properties": self.properties,
            "sources": sorted(set(self.sources)),
        }


def empty_graph() -> GraphDict:
    return {"nodes": {}, "edges": {}}

