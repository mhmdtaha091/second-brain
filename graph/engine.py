"""
Second Brain — Knowledge Graph Engine
Parses markdown notes, builds a bidirectional link graph,
computes centrality, clusters, and exports for visualization.
100% local. No cloud. Your data stays yours.
"""

import os
import re
import json
import hashlib
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Markdown Parser
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
TAG_RE = re.compile(r"(?<!\w)#([a-zA-Z][a-zA-Z0-9_-]*)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)


def parse_note(filepath: str) -> dict[str, Any] | None:
    """Parse a single markdown note into structured data."""
    try:
        raw = Path(filepath).read_text(encoding="utf-8")
    except Exception:
        return None

    rel_path = os.path.relpath(filepath)
    slug = os.path.splitext(os.path.basename(filepath))[0]

    # --- frontmatter ---
    fm = {}
    body = raw
    m = FRONTMATTER_RE.match(raw)
    if m:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            pass
        body = raw[m.end():]

    # --- strip code blocks before link/tag extraction ---
    clean_body = CODE_BLOCK_RE.sub("", body)

    # --- wikilinks ---
    links = list(set(WIKILINK_RE.findall(clean_body)))

    # --- tags ---
    tags = list(set(TAG_RE.findall(clean_body)))

    # --- headings ---
    headings = [{"level": len(h[0]), "text": h[1].strip()} for h in HEADING_RE.findall(body)]

    # --- stats ---
    word_count = len(clean_body.split())
    char_count = len(body)

    return {
        "id": hashlib.sha256(rel_path.encode()).hexdigest()[:12],
        "slug": slug,
        "path": rel_path,
        "title": fm.get("title", slug.replace("-", " ").title()),
        "tags": fm.get("tags", []) + tags,
        "links": links,
        "headings": headings,
        "frontmatter": fm,
        "word_count": word_count,
        "char_count": char_count,
        "created": fm.get("created", None),
        "updated": fm.get("updated", None),
        "summary": clean_body[:280].strip(),
        "body": body,  # kept for search indexing
    }


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

def build_graph(notes_dir: str) -> dict[str, Any]:
    """Walk the notes directory, parse everything, build a graph."""
    notes: list[dict] = []
    paths: set[str] = set()

    for root, _, files in os.walk(notes_dir):
        for f in files:
            if f.endswith(".md") and not f.startswith("."):
                fp = os.path.join(root, f)
                note = parse_note(fp)
                if note:
                    notes.append(note)
                    paths.add(note["path"])

    # --- build adjacency ---
    # slug → note lookup
    slug_map: dict[str, dict] = {n["slug"]: n for n in notes}
    # path → note lookup
    path_map: dict[str, dict] = {n["path"]: n for n in notes}

    nodes: list[dict] = []
    edges: list[dict] = []
    adjacency: dict[str, set[str]] = defaultdict(set)

    for note in notes:
        nodes.append({
            "id": note["id"],
            "label": note["title"],
            "slug": note["slug"],
            "path": note["path"],
            "tags": note["tags"],
            "word_count": note["word_count"],
            "link_count": len(note["links"]),
        })

        for link_text in note["links"]:
            # Resolve wikilink to a target note
            target_slug = link_text.split("|")[0].strip().lower().replace(" ", "-")
            target = slug_map.get(target_slug)
            if target:
                adjacency[note["id"]].add(target["id"])
                edges.append({
                    "source": note["id"],
                    "target": target["id"],
                    "label": link_text,
                })
            # also try matching by title substring
            elif target_slug not in slug_map:
                for s, sn in slug_map.items():
                    if target_slug in s or s in target_slug:
                        adjacency[note["id"]].add(sn["id"])
                        edges.append({
                            "source": note["id"],
                            "target": sn["id"],
                            "label": link_text,
                        })
                        break

    # --- compute graph metrics ---
    in_degree: dict[str, int] = defaultdict(int)
    for e in edges:
        in_degree[e["target"]] += 1

    for node in nodes:
        node["degree"] = len(adjacency[node["id"]]) + in_degree[node["id"]]
        node["out_links"] = len(adjacency[node["id"]])
        node["in_links"] = in_degree[node["id"]]

    # --- community detection (simple label propagation) ---
    communities = _label_propagation(nodes, adjacency)

    # --- clusters by tag ---
    tag_clusters: dict[str, list[str]] = defaultdict(list)
    for node in nodes:
        for tag in node["tags"]:
            tag_clusters[tag].append(node["id"])

    # --- orphans (notes with no links) ---
    orphans = [n["id"] for n in nodes if n["degree"] == 0]
    hubs = sorted(nodes, key=lambda n: n["degree"], reverse=True)[:10]

    return {
        "nodes": nodes,
        "edges": edges,
        "adjacency": {k: list(v) for k, v in adjacency.items()},
        "communities": communities,
        "tag_clusters": {k: v for k, v in tag_clusters.items() if len(v) > 1},
        "orphans": orphans,
        "hubs": [{"id": h["id"], "label": h["label"], "degree": h["degree"]} for h in hubs],
        "stats": {
            "total_notes": len(notes),
            "total_edges": len(edges),
            "total_tags": len(tag_clusters),
            "orphan_count": len(orphans),
            "generated": datetime.now().isoformat(),
        },
    }


def _label_propagation(nodes: list[dict], adjacency: dict[str, set[str]], max_iter: int = 20) -> dict[str, int]:
    """Simple label propagation for community detection."""
    labels = {n["id"]: i for i, n in enumerate(nodes)}
    for _ in range(max_iter):
        changed = False
        for node in nodes:
            nid = node["id"]
            neighbors = adjacency.get(nid, set())
            if not neighbors:
                continue
            # most common label among neighbors
            neighbor_labels = [labels.get(nb, 0) for nb in neighbors]
            most_common = max(set(neighbor_labels), key=neighbor_labels.count)
            if labels[nid] != most_common:
                labels[nid] = most_common
                changed = True
        if not changed:
            break
    # remap to contiguous integers
    unique_labels = list(set(labels.values()))
    remap = {old: new for new, old in enumerate(unique_labels)}
    return {nid: remap[lbl] for nid, lbl in labels.items()}


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_notes(notes_dir: str, query: str) -> list[dict]:
    """Full-text search across all notes."""
    results = []
    query_lower = query.lower()
    for root, _, files in os.walk(notes_dir):
        for f in files:
            if f.endswith(".md"):
                fp = os.path.join(root, f)
                note = parse_note(fp)
                if not note:
                    continue
                score = 0
                body_lower = note["body"].lower()
                title_lower = note["title"].lower()
                # title match
                if query_lower in title_lower:
                    score += 10
                # body match
                score += body_lower.count(query_lower)
                # tag match
                if any(query_lower in t.lower() for t in note["tags"]):
                    score += 5
                if score > 0:
                    results.append({
                        "id": note["id"],
                        "title": note["title"],
                        "path": note["path"],
                        "score": score,
                        "snippet": _snippet(body_lower, query_lower),
                    })
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:20]


def _snippet(text: str, query: str, radius: int = 80) -> str:
    idx = text.find(query)
    if idx < 0:
        return text[:radius * 2]
    start = max(0, idx - radius)
    end = min(len(text), idx + len(query) + radius)
    return ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")


# ---------------------------------------------------------------------------
# Export (for visualization)
# ---------------------------------------------------------------------------

def export_graph_json(notes_dir: str, out_path: str | None = None) -> str:
    """Build graph and export as JSON for the 3D viz."""
    graph = build_graph(notes_dir)
    # Remove body text to keep JSON light
    for node in graph["nodes"]:
        node.pop("body", None)
    payload = json.dumps(graph, indent=2, ensure_ascii=False)
    if out_path:
        Path(out_path).write_text(payload, encoding="utf-8")
    return payload


# ---------------------------------------------------------------------------
# CLI Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    notes_dir = sys.argv[1] if len(sys.argv) > 1 else "../notes"
    cmd = sys.argv[2] if len(sys.argv) > 2 else "export"
    if cmd == "export":
        out = sys.argv[3] if len(sys.argv) > 3 else "../viz/graph-data.json"
        export_graph_json(notes_dir, out)
        print(f"Graph exported -> {out}")
    elif cmd == "search":
        q = sys.argv[3] if len(sys.argv) > 3 else ""
        for r in search_notes(notes_dir, q):
            print(f"[{r['score']}] {r['title']} ({r['path']})")
    elif cmd == "stats":
        g = build_graph(notes_dir)
        print(json.dumps(g["stats"], indent=2))
