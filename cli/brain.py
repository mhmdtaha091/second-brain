#!/usr/bin/env python3
"""
Second Brain CLI -- your local knowledge command center.

Usage:
  brain note "Title"              Create a new note
  brain link "Note A" "Note B"    Add a wikilink from A -> B
  brain search "query"            Full-text search
  brain graph                     Regenerate graph JSON
  brain serve                     Start AR visualization server
  brain stats                     Show knowledge graph stats
  brain daily                     Create today's daily note
  brain tags                      List all tags
  brain orphans                   List unlinked notes
  brain delete "Note"             Move a note to trash
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

# Ensure UTF-8 on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from graph.project_indexer import build_full_graph
from graph.engine import parse_note, search_notes

NOTES_DIR = Path(__file__).resolve().parent.parent / "notes"
PROJECTS_ROOT = Path(__file__).resolve().parent.parent.parent  # D:/Projects
GRAPH_OUT = Path(__file__).resolve().parent.parent / "viz" / "graph-data.json"

NOW = datetime.now()
DATE_STAMP = NOW.strftime("%Y-%m-%d")
TIME_STAMP = NOW.strftime("%Y-%m-%d %H:%M")


def slugify(text: str) -> str:
    return text.lower().replace(" ", "-").replace("/", "-")


def note_path(slug: str, folder: str = "") -> Path:
    base = NOTES_DIR / folder if folder else NOTES_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{slug}.md"


def find_note(title_or_slug: str) -> Path | None:
    """Find a note by title or slug across all subdirectories."""
    for root, _, files in os.walk(NOTES_DIR):
        for f in files:
            if not f.endswith(".md"):
                continue
            fp = Path(root) / f
            note = parse_note(str(fp))
            if not note:
                continue
            if note["slug"] == slugify(title_or_slug) or note["title"].lower() == title_or_slug.lower():
                return fp
            if title_or_slug.lower() in note["title"].lower():
                return fp
    return None


def cmd_note(args):
    """Create a new note. Usage: brain note "My Title" [--folder projects] [--tag tag1,tag2]"""
    if not args:
        print("[!] Usage: brain note \"Title\" [--folder folder] [--tag tag1,tag2]")
        return

    title = args[0]
    folder = ""
    tags = []

    i = 1
    while i < len(args):
        if args[i] == "--folder" and i + 1 < len(args):
            folder = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tags = [t.strip() for t in args[i + 1].split(",")]
            i += 2
        else:
            i += 1

    slug = slugify(title)
    fp = note_path(slug, folder)

    if fp.exists():
        print(f"[!] Note already exists: {fp}")
        return

    frontmatter = f"""---
title: {title}
created: {TIME_STAMP}
updated: {TIME_STAMP}
tags: [{', '.join(tags)}]
---

# {title}

"""
    fp.write_text(frontmatter, encoding="utf-8")
    print(f"[+] Created: {fp}")
    print(f"    Tags: {tags or 'none'}")


def cmd_link(args):
    """Add a wikilink between notes. Usage: brain link "Source" "Target" """
    if len(args) < 2:
        print("[!] Usage: brain link \"Source Note\" \"Target Note\"")
        return

    src_title, tgt_title = args[0], args[1]
    src_path = find_note(src_title)
    tgt_path = find_note(tgt_title)

    if not src_path:
        print(f"[!] Source note not found: {src_title}")
        return
    if not tgt_path:
        print(f"[!] Target note not found: {tgt_title}")
        return

    tgt_note = parse_note(str(tgt_path))
    link_text = tgt_note["title"] if tgt_note else tgt_title

    content = src_path.read_text(encoding="utf-8")
    wikilink = f"[[{link_text}]]"

    if wikilink in content:
        print(f"[!] Link already exists: {wikilink}")
        return

    if "## Links" in content:
        content = content.replace("## Links", f"## Links\n- {wikilink}")
    else:
        content += f"\n\n## Links\n- {wikilink}\n"

    # Update frontmatter timestamp safely
    content = re.sub(r"^updated:.*$", f"updated: {TIME_STAMP}", content, flags=re.MULTILINE)

    src_path.write_text(content, encoding="utf-8")
    print(f"[>] Linked: {src_path.name} -> [[{link_text}]]")


def cmd_search(args):
    """Full-text search across ALL projects. Usage: brain search "query" """
    if not args:
        print("[!] Usage: brain search \"query\"")
        return
    query = args[0]
    ql = query.lower()
    g = build_full_graph(str(PROJECTS_ROOT), str(NOTES_DIR))
    results = []
    for node in g.get("nodes", []):
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
                "score": score,
                "title": node.get("label", ""),
                "path": node.get("path", node.get("type", "")),
                "project": node.get("project", ""),
                "type": node.get("type", ""),
                "snippet": node.get("summary", "")[:200],
            })
    results.sort(key=lambda r: r["score"], reverse=True)
    if not results:
        print(f"[?] No results for: {query}")
        return
    print(f"\nSearch results for \"{query}\" ({len(results)} hits):")
    print("-" * 60)
    for r in results[:25]:
        tag = f"[{r['type']}]" if r.get('type') else ""
        proj = f" @ {r['project']}" if r.get('project') else ""
        print(f"  [{r['score']}] {tag} {r['title']}{proj}")
        print(f"       {r['path']}")
        print(f"       ...{r['snippet']}...\n")


def cmd_graph(args=None):
    """Regenerate the graph JSON from all real projects."""
    g = build_full_graph(str(PROJECTS_ROOT), str(NOTES_DIR))
    GRAPH_OUT.parent.mkdir(parents=True, exist_ok=True)
    GRAPH_OUT.write_text(json.dumps(g, indent=2, ensure_ascii=False), encoding='utf-8')
    s = g["stats"]
    print(f"[*] Graph regenerated from all projects!")
    print(f"    Projects: {s.get('total_projects', '?')} | Nodes: {s['total_notes']} | Edges: {s['total_edges']}")
    print(f"    Orphans: {s['orphan_count']} | Communities: {len(g['communities'])}")
    print(f"    -> {GRAPH_OUT}")


def cmd_serve(args=None):
    """Start the local AR visualization server."""
    server_path = Path(__file__).resolve().parent.parent / "server.py"
    print("Starting Second Brain server...")
    print("  Open http://localhost:8420 in your browser")
    print("  For AR mode, use a WebXR-compatible browser")
    print("  Press Ctrl+C to stop\n")
    subprocess.run([sys.executable, str(server_path)])


def cmd_stats(args=None):
    """Show knowledge graph statistics."""
    g = build_full_graph(str(PROJECTS_ROOT), str(NOTES_DIR))
    s = g["stats"]
    print(f"\n[*] Second Brain Stats (from ALL projects)")
    print("=" * 50)
    print(f"  Projects:        {s.get('total_projects', '?')}")
    print(f"  Total Nodes:     {s['total_notes']}")
    print(f"  Total Edges:     {s['total_edges']}")
    print(f"  Unique Tags:     {s['total_tags']}")
    print(f"  Orphan Nodes:    {s['orphan_count']}")
    print(f"  Communities:     {len(g['communities'])}")
    print(f"  Generated:       {s['generated']}")
    if g["hubs"]:
        print(f"\n  *** Top Hubs:")
        for h in g["hubs"][:8]:
            print(f"     [{h['degree']}] {h['label']} ({h.get('type', '?')})")
    # Show projects
    projects = [n for n in g["nodes"] if n.get("type") == "project"]
    if projects:
        print(f"\n  *** Projects Indexed:")
        for p in sorted(projects, key=lambda x: x.get('degree', 0), reverse=True):
            print(f"     [{p.get('degree', 0)}] {p['label']}")


def cmd_daily(args=None):
    """Create today's daily note."""
    slug = DATE_STAMP
    fp = NOTES_DIR / "daily" / f"{slug}.md"
    if fp.exists():
        print(f"[*] Daily note already exists: {fp}")
        return

    frontmatter = f"""---
title: Daily -- {DATE_STAMP}
created: {TIME_STAMP}
updated: {TIME_STAMP}
tags: [daily]
---

# {DATE_STAMP}

## Today's Focus
-

## Notes
-

## Reflections
-
"""
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(frontmatter, encoding="utf-8")
    print(f"[+] Daily note created: {fp}")


def cmd_tags(args=None):
    """List all tags in the knowledge base."""
    g = build_full_graph(str(PROJECTS_ROOT), str(NOTES_DIR))
    tag_counts: dict[str, int] = {}
    for node in g["nodes"]:
        for tag in node.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    print(f"\nTags ({len(tag_counts)}):")
    print("-" * 40)
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:30]:
        bar = "#" * min(count, 20)
        print(f"  {tag:<25} {bar} {count}")


def cmd_orphans(args=None):
    """List orphan nodes (no links)."""
    g = build_full_graph(str(PROJECTS_ROOT), str(NOTES_DIR))
    orphans = [n for n in g["nodes"] if n["id"] in g["orphans"]]
    if not orphans:
        print("[*] No orphan nodes! Everything is connected.")
        return
    print(f"\nOrphan Nodes ({len(orphans)}):")
    print("-" * 40)
    for n in sorted(orphans, key=lambda x: x.get("label", "")):
        print(f"  [ ] {n.get('label','?')} ({n.get('path', n.get('type','?'))})")


def cmd_delete(args):
    """Delete a note (moves to .trash). Usage: brain delete "Note Title" """
    if not args:
        print("[!] Usage: brain delete \"Note Title\"")
        return
    fp = find_note(args[0])
    if not fp:
        print(f"[!] Note not found: {args[0]}")
        return

    trash_dir = NOTES_DIR.parent / ".trash"
    trash_dir.mkdir(exist_ok=True)
    dest = trash_dir / fp.name
    if dest.exists():
        dest = trash_dir / f"{fp.stem}_{int(datetime.now().timestamp())}.md"
    fp.rename(dest)
    print(f"[-] Moved to trash: {fp.name} -> .trash/")
    print(f"    (Recoverable from .trash/ until you empty it)")


CMDS = {
    "note": cmd_note,
    "link": cmd_link,
    "search": cmd_search,
    "graph": cmd_graph,
    "serve": cmd_serve,
    "stats": cmd_stats,
    "daily": cmd_daily,
    "tags": cmd_tags,
    "orphans": cmd_orphans,
    "delete": cmd_delete,
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Available commands:", ", ".join(CMDS.keys()))
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd in CMDS:
        CMDS[cmd](args)
    else:
        print(f"[!] Unknown command: {cmd}")
        print(f"    Available: {', '.join(CMDS.keys())}")


if __name__ == "__main__":
    main()
