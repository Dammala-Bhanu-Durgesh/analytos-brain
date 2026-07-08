from __future__ import annotations

import re
from pathlib import Path

from .graph import edge_id, stable_id, upsert_edge, upsert_node
from .models import Edge, GraphDict, Node


def line_items(section: str) -> list[str]:
    return [line[2:].strip() for line in section.splitlines() if line.strip().startswith("- ")]


def get_section(text: str, heading: str) -> str:
    pattern = rf"## {re.escape(heading)}\n(?P<body>.*?)(?=\n## |\Z)"
    match = re.search(pattern, text, re.S)
    return match.group("body").strip() if match else ""


def first_paragraph_after_title(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    body = [line for line in lines if not line.startswith("#") and ":" not in line[:24]]
    return body[0] if body else ""


def visibility(text: str) -> str:
    return "restricted" if "visibility: restricted" in text.lower() else "public"


def product_from_filename(path: Path) -> str | None:
    name = path.name.lower()
    if "stockly" in name:
        return "Stockly"
    if "inspectly" in name:
        return "Inspectly"
    return None


def ingest_product_doc(graph: GraphDict, path: Path, text: str) -> None:
    product = product_from_filename(path)
    if not product:
        return
    source = path.name
    vis = visibility(text)
    description = first_paragraph_after_title(text)
    positioning = get_section(text, "Positioning").strip()
    product_id = stable_id("Product", product)
    upsert_node(
        graph,
        Node(
            product_id,
            "Product",
            {
                "name": product,
                "description": description,
                "positioning": positioning,
                "visibility": vis,
            },
            [source],
        ),
    )
    for feature in line_items(get_section(text, "Features")):
        feature_name = feature.split(" that ")[0].split(" using ")[0].strip(".")
        feature_id = stable_id("Feature", product, feature_name)
        upsert_node(
            graph,
            Node(feature_id, "Feature", {"name": feature_name, "description": feature, "visibility": vis}, [source]),
        )
        upsert_edge(graph, Edge(edge_id("HAS_FEATURE", product_id, feature_id), "HAS_FEATURE", product_id, feature_id, {}, (source,)))
    for proof in line_items(get_section(text, "Proof points")):
        proof_id = stable_id("ProofPoint", product, proof)
        metric = extract_metric(proof)
        upsert_node(
            graph,
            Node(proof_id, "ProofPoint", {"metric": metric, "value": proof, "context": product, "visibility": vis}, [source]),
        )
        upsert_edge(graph, Edge(edge_id("PROVEN_BY", product_id, proof_id), "PROVEN_BY", product_id, proof_id, {}, (source,)))
    for persona in line_items(get_section(text, "Target users")):
        persona_id = stable_id("Persona", persona)
        upsert_node(graph, Node(persona_id, "Persona", {"name": persona, "owns": "", "visibility": vis}, [source]))
        upsert_edge(graph, Edge(edge_id("SERVES_PERSONA", product_id, persona_id), "SERVES_PERSONA", product_id, persona_id, {}, (source,)))


def extract_metric(text: str) -> str:
    match = re.search(r"(\d+%|\d+\s*stores?|\d+\s*weeks?|above\s+\d+%)", text, re.I)
    return match.group(1) if match else text.split()[0]


def ingest_icp_doc(graph: GraphDict, path: Path, text: str) -> None:
    source = path.name
    vis = visibility(text)
    for segment_name in re.findall(r"### (.+)", text):
        block = re.search(rf"### {re.escape(segment_name)}\n(?P<body>.*?)(?=\n### |\n## |\Z)", text, re.S)
        body = block.group("body") if block else ""
        props = {"name": segment_name, "firmographics": "", "triggers": "", "competitors": "", "visibility": vis}
        best_products: list[str] = []
        for item in line_items(body):
            key, _, value = item.partition(":")
            normalized = key.lower()
            if normalized == "company size":
                props["firmographics"] = value.strip()
            elif normalized == "triggers":
                props["triggers"] = value.strip()
            elif normalized == "competitors displaced":
                props["competitors"] = value.strip()
            elif normalized == "best products":
                best_products = [p.strip().strip(".") for p in value.split(",")]
        segment_id = stable_id("ICPSegment", segment_name)
        upsert_node(graph, Node(segment_id, "ICPSegment", props, [source]))
        for product in best_products:
            product_id = stable_id("Product", product)
            upsert_edge(graph, Edge(edge_id("TARGETS", product_id, segment_id), "TARGETS", product_id, segment_id, {}, (source,)))
    for item in line_items(get_section(text, "Personas")):
        name, _, owns = item.partition(":")
        upsert_node(
            graph,
            Node(stable_id("Persona", name), "Persona", {"name": name.strip(), "owns": owns.strip(), "visibility": vis}, [source]),
        )


def ingest_email_doc(graph: GraphDict, path: Path, text: str) -> None:
    source = path.name
    product = product_from_filename(path) or "Analytos"
    subject_match = re.search(r"Subject:\s*(.+)", text)
    subject = subject_match.group(1).strip() if subject_match else path.stem
    thread_id = stable_id("EmailThread", subject)
    summary = first_paragraph_after_title(text)
    upsert_node(
        graph,
        Node(thread_id, "EmailThread", {"subject": subject, "summary": summary, "classification": "internal-only", "visibility": "restricted"}, [source]),
    )
    product_id = stable_id("Product", product)
    upsert_edge(graph, Edge(edge_id("DISCUSSED_IN", product_id, thread_id), "DISCUSSED_IN", product_id, thread_id, {}, (source,)))
    decision_match = re.search(r"Decision:\s*(.+)", text)
    if decision_match:
        decision = decision_match.group(1).strip()
        decision_id = stable_id("Decision", subject, decision)
        upsert_node(graph, Node(decision_id, "Decision", {"statement": decision, "visibility": "restricted"}, [source]))
        upsert_edge(graph, Edge(edge_id("THREAD_DECISION", thread_id, decision_id), "THREAD_DECISION", thread_id, decision_id, {}, (source,)))
    people_block = get_section(text, "People involved")
    for item in line_items(people_block):
        name, _, role = item.partition(",")
        person_id = stable_id("Person", name)
        upsert_node(graph, Node(person_id, "Person", {"name": name.strip(), "role": role.strip(), "visibility": "restricted"}, [source]))


def ingest_markdown(graph: GraphDict, path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if path.name == "icp-analytos.md":
        ingest_icp_doc(graph, path, text)
    elif path.name.startswith("email-"):
        ingest_email_doc(graph, path, text)
    else:
        ingest_product_doc(graph, path, text)

