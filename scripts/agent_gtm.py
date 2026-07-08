from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brain.search import entities, search
from brain.storage import load_branch


EXAMPLE_COMPANIES = {
    "Stockly": ["RegionalMart", "FreshLane Grocery", "OmniHome Retail"],
    "Inspectly": ["MedNova Devices", "CareTrace Labs", "SterileWorks Manufacturing"],
}


def product_from_prompt(prompt: str) -> str:
    lowered = prompt.lower()
    if "inspectly" in lowered:
        return "Inspectly"
    return "Stockly"


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or "who should we prospect for Stockly"
    product = product_from_prompt(prompt)
    grouped = entities("gtm-agent")
    graph = load_branch("main")
    product_ids = [node["id"] for node in graph["nodes"].values() if node["type"] == "Product" and node["properties"].get("name") == product]
    target_ids = {
        edge["to"]
        for edge in graph["edges"].values()
        if edge["type"] == "TARGETS" and edge["from"] in product_ids
    }
    segments = [node for node in grouped.get("ICPSegment", []) if node["id"] in target_ids]
    personas = grouped.get("Persona", [])
    proofs = [node for node in grouped.get("ProofPoint", []) if product.lower() in node["properties"].get("context", "").lower()]
    if not segments:
        segments = search("gtm-agent", product, limit=5)

    print(f"# Prospecting Brief: {product}\n")
    print("## Target company profile\n")
    for segment in segments[:2]:
        props = segment["properties"]
        print(f"- Segment: {props.get('name', segment['id'])}")
        if props.get("firmographics"):
            print(f"- Firmographics: {props['firmographics']}")
        if props.get("triggers"):
            print(f"- Trigger signals: {props['triggers']}")
        if props.get("competitors"):
            print(f"- Displacement angle: replace {props['competitors']}")
    print("\n## Example accounts\n")
    for company in EXAMPLE_COMPANIES.get(product, []):
        print(f"- {company}")
    print("\n## Persona to contact\n")
    for persona in personas:
        name = persona["properties"].get("name", "")
        owns = persona["properties"].get("owns", "")
        if product == "Stockly" and any(token in name for token in ["Inventory", "VP of Operations", "Store Operations", "Supply Chain"]):
            print(f"- {name}: {owns or 'owns operational reliability and throughput'}")
        if product == "Inspectly" and any(token in name for token in ["Quality", "Compliance", "Inspection"]):
            print(f"- {name}: {owns or 'owns audit readiness and compliance evidence'}")
    print("\n## Opening angle grounded in proof points\n")
    for proof in proofs[:3]:
        print(f"- Lead with: {proof['properties']['value']}")
    print("\n## Policy check\n")
    blocked = search("gtm-agent", "internal email thread", limit=10)
    print(f"- gtm-agent restricted EmailThread access: {'blocked as expected' if not any(n['type'] == 'EmailThread' for n in blocked) else 'FAILED'}")


if __name__ == "__main__":
    main()
