"""
Second Brain — Local Server
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
NOTES_DIR = ROOT / "notes"
VIZ_DIR = ROOT / "viz"
GRAPH_FILE = VIZ_DIR / "graph-data.json"

sys.path.insert(0, str(ROOT))
from graph.engine import build_graph, export_graph_json, search_notes, parse_note


class BrainHandler(SimpleHTTPRequestHandler):
    """Custom handler: serves static files + REST API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # --- API Routes ---
        if path == "/api/graph":
            self._json_response(export_graph_json(str(NOTES_DIR)))
            return

        if path == "/api/stats":
            g = build_graph(str(NOTES_DIR))
            self._json_response(g["stats"])
            return

        if path == "/api/search":
            q = parse_qs(parsed.query).get("q", [""])[0]
            results = search_notes(str(NOTES_DIR), q)
            self._json_response(results)
            return

        if path.startswith("/api/note/"):
            note_path_rel = path[len("/api/note/"):]
            note_path = NOTES_DIR / note_path_rel
            if note_path.exists():
                note = parse_note(str(note_path))
                if note:
                    self._json_response(note)
                    return
            self._json_response({"error": "not found"}, 404)
            return

        if path == "/api/tags":
            g = build_graph(str(NOTES_DIR))
            tag_map = {}
            for node in g["nodes"]:
                for tag in node["tags"]:
                    tag_map.setdefault(tag, []).append(node["id"])
            self._json_response(tag_map)
            return

        # --- Serve static files ---
        # Redirect root to /viz/
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
        # Quieter logging
        if "/api/" in str(args[0]):
            print(f"  ⚡ {args[0]}")
        else:
            pass  # suppress static file noise


def main():
    port = 8420

    # Ensure graph data is fresh
    print("🧠 Building knowledge graph...")
    export_graph_json(str(NOTES_DIR), str(GRAPH_FILE))

    # Start server
    server = HTTPServer(("127.0.0.1", port), BrainHandler)
    print(f"\n{'═'*55}")
    print(f"  🧠 SECOND BRAIN — LIVE")
    print(f"  Local: http://localhost:{port}")
    print(f"  AR Mode: Open on phone/AR headset browser")
    print(f"  Press Ctrl+C to stop")
    print(f"{'═'*55}\n")

    webbrowser.open(f"http://localhost:{port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down. Your knowledge is safe.")
        server.server_close()


if __name__ == "__main__":
    main()
