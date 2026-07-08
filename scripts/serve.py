from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brain.graph import diff_graph, merge_branch, reject_branch
from brain.search import entities, recent_changes, search
from brain.storage import latest_branch, list_branches, load_branch


HOST = "127.0.0.1"
PORT = 8080


def html_page() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Analytos Brain</title>
  <style>
    :root { color-scheme: light; --ink:#172026; --muted:#5c6975; --line:#d9e0e6; --accent:#006b5f; --soft:#eef7f5; --warn:#7a3f00; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Arial, sans-serif; color:var(--ink); background:#f8fafb; }
    header { background:#ffffff; border-bottom:1px solid var(--line); padding:20px 32px; display:flex; gap:16px; align-items:center; justify-content:space-between; }
    h1 { margin:0; font-size:24px; letter-spacing:0; }
    main { padding:24px 32px; display:grid; grid-template-columns: 1.2fr .8fr; gap:20px; }
    section { background:#ffffff; border:1px solid var(--line); border-radius:8px; padding:18px; }
    h2 { margin:0 0 12px; font-size:17px; }
    input, select, button { font:inherit; border:1px solid var(--line); border-radius:6px; padding:9px 10px; background:#fff; }
    button { background:var(--accent); color:#fff; border-color:var(--accent); cursor:pointer; }
    button.secondary { background:#fff; color:var(--accent); }
    .toolbar { display:flex; gap:8px; margin-bottom:12px; flex-wrap:wrap; }
    .grid { display:grid; gap:10px; }
    .node { border:1px solid var(--line); border-radius:6px; padding:12px; background:#fff; }
    .type { color:var(--accent); font-size:12px; font-weight:700; text-transform:uppercase; }
    .muted { color:var(--muted); font-size:13px; }
    pre { white-space:pre-wrap; overflow:auto; background:#101820; color:#f5fbff; padding:12px; border-radius:6px; max-height:420px; }
    .status { color:var(--warn); font-weight:700; }
    @media (max-width: 900px) { main { grid-template-columns: 1fr; padding:16px; } header { padding:16px; align-items:flex-start; flex-direction:column; } }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Analytos Brain</h1>
      <div class="muted">Governed context layer: branch, review, merge, dashboard, MCP access.</div>
    </div>
    <div class="toolbar">
      <button onclick="loadEntities()">Refresh</button>
      <button class="secondary" onclick="loadReview()">Review Latest</button>
    </div>
  </header>
  <main>
    <section>
      <h2>Entity Browser</h2>
      <div class="toolbar">
        <select id="actor">
          <option value="dashboard">dashboard</option>
          <option value="content-agent">content-agent</option>
          <option value="gtm-agent">gtm-agent</option>
          <option value="reviewer">reviewer</option>
        </select>
        <input id="query" placeholder="Search approved knowledge" onkeydown="if(event.key==='Enter') doSearch()">
        <button onclick="doSearch()">Search</button>
      </div>
      <div id="entities" class="grid"></div>
    </section>
    <section>
      <h2>Recent Changes</h2>
      <div id="changes" class="grid"></div>
    </section>
    <section>
      <h2>HITL Review</h2>
      <div class="toolbar">
        <input id="reviewer" value="reviewer@santosh">
        <button onclick="approve()">Approve and Merge</button>
        <button class="secondary" onclick="reject()">Reject</button>
      </div>
      <pre id="review">No branch loaded.</pre>
    </section>
    <section>
      <h2>MCP Query</h2>
      <div class="toolbar">
        <select id="mcpActor">
          <option value="content-agent">content-agent</option>
          <option value="gtm-agent">gtm-agent</option>
          <option value="reviewer">reviewer</option>
        </select>
        <input id="mcpQuery" value="inventory accuracy">
        <button onclick="mcpSearch()">Run</button>
      </div>
      <pre id="mcpResult"></pre>
    </section>
  </main>
  <script>
    async function api(path, options) {
      const response = await fetch(path, options);
      return response.json();
    }
    function renderNode(node) {
      const props = node.properties || {};
      const title = props.name || props.subject || props.metric || node.id;
      const desc = props.description || props.value || props.positioning || props.summary || props.statement || props.triggers || "";
      return `<div class="node"><div class="type">${node.type}</div><strong>${title}</strong><div class="muted">${desc}</div><div class="muted">sources: ${(node.sources || []).join(", ")}</div></div>`;
    }
    async function loadEntities() {
      const actor = document.getElementById("actor").value;
      const data = await api(`/api/entities?actor=${actor}`);
      document.getElementById("entities").innerHTML = Object.entries(data).map(([kind, nodes]) => `<h2>${kind}</h2>${nodes.map(renderNode).join("")}`).join("");
      const changes = await api("/api/changes");
      document.getElementById("changes").innerHTML = changes.map(c => `<div class="node"><strong>${c.branch}</strong><div class="muted">${c.timestamp} by ${c.actor}</div><div class="muted">${JSON.stringify(c.summary)}</div></div>`).join("") || "<div class='muted'>No commits yet.</div>";
    }
    async function doSearch() {
      const actor = document.getElementById("actor").value;
      const query = encodeURIComponent(document.getElementById("query").value);
      const data = await api(`/api/search?actor=${actor}&q=${query}`);
      document.getElementById("entities").innerHTML = data.map(renderNode).join("") || "<div class='muted'>No results.</div>";
    }
    async function loadReview() {
      const data = await api("/api/review/latest");
      document.getElementById("review").textContent = JSON.stringify(data, null, 2);
    }
    async function approve() {
      const actor = document.getElementById("reviewer").value;
      const data = await api("/api/review/approve", {method:"POST", body:JSON.stringify({actor})});
      document.getElementById("review").textContent = JSON.stringify(data, null, 2);
      loadEntities();
    }
    async function reject() {
      const actor = document.getElementById("reviewer").value;
      const data = await api("/api/review/reject", {method:"POST", body:JSON.stringify({actor})});
      document.getElementById("review").textContent = JSON.stringify(data, null, 2);
      loadEntities();
    }
    async function mcpSearch() {
      const actor = document.getElementById("mcpActor").value;
      const query = document.getElementById("mcpQuery").value;
      const data = await api("/api/mcp/query", {method:"POST", body:JSON.stringify({actor, tool:"search", query})});
      document.getElementById("mcpResult").textContent = JSON.stringify(data, null, 2);
    }
    loadEntities();
  </script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def _json(self, data: object, status: int = 200) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == "/":
            body = html_page().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif parsed.path == "/api/entities":
            actor = qs.get("actor", ["dashboard"])[0]
            self._json(entities(actor))
        elif parsed.path == "/api/search":
            actor = qs.get("actor", ["dashboard"])[0]
            query = qs.get("q", [""])[0]
            self._json(search(actor, query))
        elif parsed.path == "/api/changes":
            self._json(recent_changes())
        elif parsed.path == "/api/review/latest":
            branch = latest_branch()
            if not branch:
                self._json({"error": "no latest branch"}, 404)
            else:
                self._json({"branch": branch, "diff": diff_graph(load_branch("main"), load_branch(branch))})
        elif parsed.path == "/api/mcp/tools":
            self._json({"tools": [{"name": "search"}, {"name": "entities"}, {"name": "recent_changes"}]})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        parsed = urlparse(self.path)
        branch = latest_branch()
        if parsed.path == "/api/review/approve":
            if not branch:
                self._json({"error": "no latest branch"}, 404)
            else:
                self._json(merge_branch(branch, payload.get("actor", "reviewer")))
        elif parsed.path == "/api/review/reject":
            if not branch:
                self._json({"error": "no latest branch"}, 404)
            else:
                self._json(reject_branch(branch, payload.get("actor", "reviewer")))
        elif parsed.path == "/api/mcp/query":
            actor = payload.get("actor", "content-agent")
            tool = payload.get("tool", "search")
            if tool == "search":
                self._json({"actor": actor, "results": search(actor, payload.get("query", ""), limit=20)})
            elif tool == "entities":
                self._json({"actor": actor, "results": entities(actor)})
            elif tool == "recent_changes":
                self._json({"actor": actor, "results": recent_changes()})
            else:
                self._json({"error": f"unknown tool {tool}"}, 400)
        else:
            self._json({"error": "not found"}, 404)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Analytos Brain dashboard: http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()

