"""
Second Brain -- Local Server
Serves the 3D/AR knowledge graph visualization and REST API.
100% local. No telemetry. No cloud. Your data never leaves your machine.
"""

import os
import sys
import json
import webbrowser
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
PROJECTS_ROOT = ROOT.parent  # D:/Projects
VIZ_DIR = ROOT / "viz"
GRAPH_FILE = VIZ_DIR / "graph-data.json"

sys.path.insert(0, str(ROOT))
from graph.project_indexer import build_full_graph
from graph.engine import search_notes


def load_graph():
    """Load pre-built graph, or regenerate if missing."""
    if GRAPH_FILE.exists():
        try:
            with open(GRAPH_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    # Regenerate
    graph = build_full_graph(str(PROJECTS_ROOT), str(ROOT / "notes"))
    GRAPH_FILE.parent.mkdir(parents=True, exist_ok=True)
    GRAPH_FILE.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding='utf-8')
    return graph


class BrainHandler(SimpleHTTPRequestHandler):
    """Custom handler: static files + REST API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # --- API Routes ---
        if path == "/api/graph":
            graph = load_graph()
            self._json_response(graph)
            return

        if path == "/api/refresh":
            print("  [*] Regenerating knowledge graph from all projects...")
            graph = build_full_graph(str(PROJECTS_ROOT), str(ROOT / "notes"))
            GRAPH_FILE.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding='utf-8')
            self._json_response({"ok": True, "stats": graph["stats"]})
            return

        if path == "/api/stats":
            graph = load_graph()
            self._json_response(graph.get("stats", {}))
            return

        if path == "/api/search":
            q = parse_qs(parsed.query).get("q", [""])[0]
            graph = load_graph()
            # Search through node labels, tags, and summaries
            results = []
            ql = q.lower()
            for node in graph.get("nodes", []):
                score = 0
                if ql in node.get("label", "").lower():
                    score += 10
                if ql in node.get("summary", "").lower():
                    score += 3
                for tag in node.get("tags", []):
                    if ql in tag.lower():
                        score += 5
                if score > 0:
                    results.append({
                        "id": node["id"],
                        "title": node["label"],
                        "path": node.get("path", ""),
                        "project": node.get("project", ""),
                        "type": node.get("type", ""),
                        "score": score,
                        "snippet": node.get("summary", "")[:200],
                    })
            results.sort(key=lambda r: r["score"], reverse=True)
            self._json_response(results[:30])
            return

        if path == "/api/tags":
            graph = load_graph()
            tag_map = {}
            for node in graph.get("nodes", []):
                for tag in node.get("tags", []):
                    tag_map.setdefault(tag, []).append(node["id"])
            self._json_response(tag_map)
            return

        if path == "/api/projects":
            graph = load_graph()
            projects = [n for n in graph.get("nodes", []) if n.get("type") == "project"]
            self._json_response(projects)
            return

        # --- Serve static files ---
        if path == "/" or path == "":
            self.send_response(302)
            self.send_header("Location", "/viz/")
            self.end_headers()
            return

        return super().do_GET()

    def _json_response(self, data, code=200):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if "/api/" in str(args[0]):
            print(f"  API: {args[0]}")
        else:
            pass


def main():
    port = 8420

    # Pre-load the graph
    print("[*] Building knowledge graph from your real projects...")
    graph = load_graph()
    s = graph.get("stats", {})
    print(f"    {s.get('total_projects', '?')} projects, {s.get('total_notes', '?')} nodes, {s.get('total_edges', '?')} edges")

    server = HTTPServer(("127.0.0.1", port), BrainHandler)
    print(f"\n{'='*55}")
    print(f"  SECOND BRAIN -- LIVE")
    print(f"  http://localhost:{port}")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*55}\n")

    webbrowser.open(f"http://localhost:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down. Your knowledge is safe.")
        server.server_close()


if __name__ == "__main__":
    main()
