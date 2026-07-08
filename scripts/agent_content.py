from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brain.search import entities, search


def product_from_prompt(prompt: str, hits: list[dict]) -> str:
    lowered = prompt.lower()
    if any(word in lowered for word in ["stock", "inventory", "shelf", "replenishment", "retail"]):
        return "Stockly"
    if any(word in lowered for word in ["inspect", "audit", "compliance", "corrective", "quality"]):
        return "Inspectly"
    product_hits = [h for h in hits if h["type"] == "Product"]
    if product_hits:
        return product_hits[0]["properties"].get("name", "Analytos")
    return "Analytos"


def main() -> None:
    topic = " ".join(sys.argv[1:]) or "write a blog post about inventory accuracy"
    hits = search("content-agent", topic, limit=12)
    grouped = entities("content-agent")
    product_name = product_from_prompt(topic, hits)
    proof_points = [p for p in grouped.get("ProofPoint", []) if p["properties"].get("context") == product_name][:5]
    features = [
        f for f in grouped.get("Feature", [])
        if product_name.lower() in f["id"] or product_name.lower() in " ".join(f.get("sources", [])).lower()
    ][:5]
    blocked_email = any(node["type"] == "EmailThread" for node in search("content-agent", "pilot email thread", limit=20))

    print(f"# Blog Draft: Turning Operational Signals into Daily Action with {product_name}\n")
    print(
        f"{product_name} helps operations teams move from stale dashboards to governed decisions. "
        "The product layer combines approved product facts, structured features, and traceable proof points so teams can act without hand-pasting context into every workflow.\n"
    )
    print("## Why this matters\n")
    print(
        "Operational teams usually have plenty of data, but the useful facts are scattered across systems, spreadsheets, and internal threads. "
        f"{product_name} gives teams one approved source of truth for the decisions that matter most.\n"
    )
    print("## Product facts from the graph\n")
    for feature in features[:3]:
        print(f"- {feature['properties']['description']}")
    for proof in proof_points[:3]:
        print(f"- Proof point: {proof['properties']['value']}")
    print("\n## Draft close\n")
    print(
        "When approved knowledge is captured as a governed graph, every downstream agent can cite the same facts, avoid stale claims, and keep sensitive context out of public-facing work."
    )
    print("\n## Policy check\n")
    print(f"- content-agent EmailThread access: {'FAILED' if blocked_email else 'blocked as expected'}")
    print(f"- approved node count visible to content-agent: {sum(len(v) for v in grouped.values())}")


if __name__ == "__main__":
    main()
