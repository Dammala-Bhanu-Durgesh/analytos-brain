# Analytos Brain on Omnigraph

Working proof-of-concept for a governed Analytos context layer: ingest seed documents, extract typed knowledge, write to an isolated branch, review/approve the diff, merge to `main`, serve approved knowledge to humans and agents, and enforce role-scoped reads.

This repo is intentionally dependency-light for the candidate walkthrough. The local runtime in `src/brain/` simulates the Omnigraph branch/review/read loop with JSON files so the demo works anywhere. The Omnigraph-facing artifacts are included in `omnigraph/`:

- `schema.pg`
- `queries/*.gq`
- `cedar.policy`
- `cluster.yaml`

## Quick Start

```powershell
python scripts/reset_demo.py
python scripts/ingest.py --source seed-data
python scripts/review.py list
python scripts/review.py approve --branch ingest/latest --actor reviewer@santosh
python scripts/agent_content.py "write a blog post about inventory accuracy"
python scripts/agent_gtm.py "who should we prospect for Stockly"
python scripts/serve.py
```

Open the dashboard at [http://127.0.0.1:8080](http://127.0.0.1:8080).

## Demo Flow

1. Reset the graph.
2. Ingest all five required seed documents into a new branch.
3. Open the review diff and approve the branch into `main`.
4. Show dashboard entity browser, search, and recent changes.
5. Run the content agent and confirm it uses only approved product/proof-point knowledge.
6. Run the GTM agent and confirm it grounds prospecting advice in ICP and proof-point nodes.
7. Demonstrate policy blocking: `content-agent` cannot read `EmailThread` nodes, while `gtm-agent` can read products, personas, ICP segments, features, and proof points.

## Required Seed Files

The assignment referenced these files in `seed-data/`; this repo includes them:

- `stockly-product-overview.md`
- `inspectly-product-overview.md`
- `icp-analytos.md`
- `email-01-stockly-pilot-thread.md`
- `email-02-inspectly-medical-thread.md`

## Architecture

```text
seed-data/*.md
   -> scripts/ingest.py
   -> deterministic extractor + idempotent upsert mutations
   -> branch: ingest/<run-id>
   -> scripts/review.py / dashboard review endpoint
   -> merge to main with actor attribution
   -> scripts/serve.py dashboard + MCP-style JSON API
   -> agent scripts
```

## Governance Guarantees

- Ingestion never writes to `main`.
- Every run writes to an isolated branch.
- Nodes are keyed by stable IDs, so re-ingesting the same files is idempotent.
- Merges require an approving actor.
- Commits record branch, actor, timestamp, added/changed counts, and source document IDs.
- Agent reads pass through the same policy gate as dashboard API reads.

## Local MCP-Style API

The server exposes MCP-like JSON endpoints suitable for a thin wrapper around `@modernrelay/omnigraph-mcp` or any MCP client:

- `GET /api/mcp/tools`
- `POST /api/mcp/query`

Example:

```powershell
$body = @{ actor = "content-agent"; tool = "search"; query = "inventory accuracy" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/api/mcp/query -ContentType application/json -Body $body
```

## Hosted Deployment Notes

For the final submission email, add:

- Dashboard URL
- MCP endpoint URL
- Shared demo credentials
- 5-minute video link
- Latest resume link

Those are candidate-specific and cannot be generated from this local workspace alone.

