"""
Project Indexer — scans real project directories and extracts
structured knowledge: project identity, tech stack, key concepts,
dependencies, and cross-project connections.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from collections import defaultdict
from typing import Any

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

# Directories to skip entirely
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    ".claude", "second-brain", "ComfyUI",  # third-party
    ".pytest_cache", "dist", "build", ".next",
    "models", "checkpoints", "output", "outputs",
    "chroma_db", "vectorstore", "data",
}

# Files that identify a project
IDENTITY_FILES = [
    "README.md", "CLAUDE.md", "AGENTS.md",
    "package.json", "pyproject.toml", "setup.py",
    "go.mod", "Cargo.toml", "Makefile",
    "docker-compose.yml", "docker-compose.yaml",
]

# Technology indicators in package.json
NPM_TECH_MAP = {
    "react": "React", "next": "Next.js", "vue": "Vue",
    "svelte": "Svelte", "angular": "Angular",
    "express": "Express", "fastify": "Fastify",
    "tailwindcss": "Tailwind", "three": "Three.js",
    "tensorflow": "TensorFlow", "pytorch": "PyTorch",
    "langchain": "LangChain", "openai": "OpenAI",
    "anthropic": "Anthropic", "google-generative-ai": "Gemini",
    "electron": "Electron", "react-native": "React Native",
    "expo": "Expo", "django": "Django", "flask": "Flask",
    "fastapi": "FastAPI", "next-auth": "NextAuth",
    "prisma": "Prisma", "drizzle": "Drizzle",
    "mediapipe": "MediaPipe", "opencv": "OpenCV",
    "puppeteer": "Puppeteer", "playwright": "Playwright",
    "socket.io": "Socket.io", "ws": "WebSocket",
    "redis": "Redis", "mongodb": "MongoDB",
    "postgres": "PostgreSQL", "sqlite": "SQLite",
}

PYTHON_TECH_MAP = {
    "flask": "Flask", "fastapi": "FastAPI", "django": "Django",
    "streamlit": "Streamlit", "gradio": "Gradio",
    "langchain": "LangChain", "llama-index": "LlamaIndex",
    "openai": "OpenAI", "anthropic": "Anthropic",
    "google-generativeai": "Gemini", "google-genai": "Gemini",
    "transformers": "HuggingFace", "torch": "PyTorch",
    "tensorflow": "TensorFlow", "jax": "JAX",
    "opencv-python": "OpenCV", "mediapipe": "MediaPipe",
    "pandas": "Pandas", "numpy": "NumPy",
    "selenium": "Selenium", "playwright": "Playwright",
    "rich": "Rich", "textual": "Textual",
    "pydantic": "Pydantic", "sqlalchemy": "SQLAlchemy",
    "alembic": "Alembic", "celery": "Celery",
    "redis": "Redis", "pymongo": "MongoDB",
    "psycopg2": "PostgreSQL", "chromadb": "ChromaDB",
    "qdrant": "Qdrant", "pinecone": "Pinecone",
    "beautifulsoup4": "BeautifulSoup", "scrapy": "Scrapy",
    "networkx": "NetworkX", "plotly": "Plotly",
    "dash": "Dash", "panel": "Panel",
}


def should_skip(path: str) -> bool:
    parts = set(Path(path).parts)
    return bool(parts & SKIP_DIRS) or any(p.startswith('.') for p in parts)


def read_file_safe(filepath: str) -> str | None:
    try:
        return Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


# ──────────────────────────────────────────────
# Project identity extraction
# ──────────────────────────────────────────────

def extract_project_identity(project_dir: str) -> dict[str, Any]:
    """Extract what a project IS from its key files."""
    info = {
        "name": os.path.basename(project_dir),
        "description": "",
        "purpose": [],
        "tech_stack": set(),
        "tags": set(),
        "entry_points": [],
        "dependencies": [],
    }

    # Read README.md
    readme_path = os.path.join(project_dir, "README.md")
    if os.path.exists(readme_path):
        content = read_file_safe(readme_path)
        if content:
            first_lines = content[:2000]
            # Extract first heading as description
            heading_match = re.search(r"^#\s+(.+)", first_lines, re.MULTILINE)
            if heading_match:
                info["description"] = heading_match.group(1).strip()
            # Extract purpose lines (bullet points after description)
            bullets = re.findall(r"^[-*]\s+(.+)", first_lines, re.MULTILINE)
            info["purpose"] = bullets[:8]

    # Read CLAUDE.md / AGENTS.md
    for fname in ["CLAUDE.md", "AGENTS.md"]:
        fp = os.path.join(project_dir, fname)
        if os.path.exists(fp):
            content = read_file_safe(fp)
            if content:
                # Extract key phrases
                info["tags"].add("has-claude-config")
                if "agent" in content.lower():
                    info["tags"].add("ai-agent")

    # Read package.json
    pkg_path = os.path.join(project_dir, "package.json")
    if os.path.exists(pkg_path):
        content = read_file_safe(pkg_path)
        if content:
            try:
                pkg = json.loads(content)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                for dep in deps:
                    if dep in NPM_TECH_MAP:
                        info["tech_stack"].add(NPM_TECH_MAP[dep])
                if pkg.get("scripts"):
                    info["entry_points"] = list(pkg["scripts"].keys())[:5]
            except json.JSONDecodeError:
                pass

    # Read requirements.txt or pyproject.toml
    for req_file in ["requirements.txt", "requirements-dev.txt"]:
        fp = os.path.join(project_dir, req_file)
        if os.path.exists(fp):
            content = read_file_safe(fp)
            if content:
                for line in content.splitlines():
                    pkg_name = re.split(r"[=<>~!\[\s]", line.strip())[0].lower()
                    if pkg_name in PYTHON_TECH_MAP:
                        info["tech_stack"].add(PYTHON_TECH_MAP[pkg_name])

    # Detect project type
    if os.path.exists(os.path.join(project_dir, "next.config.js")) or \
       os.path.exists(os.path.join(project_dir, "next.config.mjs")):
        info["tags"].add("nextjs")
    if os.path.exists(os.path.join(project_dir, "tailwind.config.js")) or \
       os.path.exists(os.path.join(project_dir, "tailwind.config.ts")):
        info["tags"].add("tailwind")
    if os.path.exists(os.path.join(project_dir, "Dockerfile")):
        info["tags"].add("dockerized")
    if os.path.exists(os.path.join(project_dir, "docker-compose.yml")) or \
       os.path.exists(os.path.join(project_dir, "docker-compose.yaml")):
        info["tags"].add("docker-compose")
    if os.path.exists(os.path.join(project_dir, "tsconfig.json")):
        info["tags"].add("typescript")
    if os.path.exists(os.path.join(project_dir, ".github")):
        info["tags"].add("ci-cd")

    info["tech_stack"] = sorted(info["tech_stack"])
    info["tags"] = sorted(info["tags"])
    return info


# ──────────────────────────────────────────────
# Scan all markdown files for knowledge extraction
# ──────────────────────────────────────────────

def scan_markdown_files(projects_root: str, max_files_per_project: int = 200) -> list[dict]:
    """Scan all .md files across projects, extracting frontmatter and structure.
    Capped per project to keep graph manageable."""
    results = []
    total = 0

    for project_name in sorted(os.listdir(projects_root)):
        project_dir = os.path.join(projects_root, project_name)
        if not os.path.isdir(project_dir):
            continue
        if project_name in SKIP_DIRS or project_name.startswith('.'):
            continue

        file_count = 0
        for root, dirs, files in os.walk(project_dir):
            # Skip unwanted dirs
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]

            for f in sorted(files):
                if not f.endswith('.md'):
                    continue
                if file_count >= max_files_per_project:
                    break

                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, projects_root)
                content = read_file_safe(fp)
                if not content or len(content) < 50:
                    continue

                # Extract frontmatter
                fm = {}
                body = content
                fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
                if fm_match:
                    try:
                        import yaml
                        fm = yaml.safe_load(fm_match.group(1)) or {}
                    except Exception:
                        pass
                    body = content[fm_match.end():]

                # Extract title from first heading
                title = f.replace('.md', '').replace('-', ' ').replace('_', ' ')
                heading_match = re.search(r"^#\s+(.+)", body, re.MULTILINE)
                if heading_match:
                    title = heading_match.group(1).strip()

                # Extract wikilinks
                wiki_links = list(set(re.findall(r"\[\[([^\]]+)\]\]", body)))

                # Extract tags
                tags = list(set(re.findall(r"(?<!\w)#([a-zA-Z][a-zA-Z0-9_-]*)", body)))
                if fm.get("tags"):
                    tags = list(set(tags + fm["tags"]))

                # Project affiliation
                project = rel.split(os.sep)[0]

                results.append({
                    "type": "note",
                    "id": hashlib.sha256(rel.encode()).hexdigest()[:12],
                    "title": title[:80],
                    "path": rel,
                    "project": project,
                    "tags": tags[:20],
                    "links": wiki_links[:30],
                    "word_count": len(body.split()),
                    "summary": body[:300].strip(),
                    "frontmatter": fm,
                })

                file_count += 1
                total += 1

    return results


# ──────────────────────────────────────────────
# Build comprehensive knowledge graph
# ──────────────────────────────────────────────

def build_full_graph(projects_root: str, notes_dir: str | None = None) -> dict:
    """Build the complete knowledge graph from all real data."""

    # 1. Index all projects
    project_nodes = []
    for name in sorted(os.listdir(projects_root)):
        pdir = os.path.join(projects_root, name)
        if not os.path.isdir(pdir) or name in SKIP_DIRS or name.startswith('.'):
            continue
        identity = extract_project_identity(pdir)
        identity["type"] = "project"
        identity["id"] = hashlib.sha256(f"project:{name}".encode()).hexdigest()[:12]
        project_nodes.append(identity)

    # 2. Scan markdown files across all projects
    note_nodes = scan_markdown_files(projects_root)

    # 3. Also index the personal notes directory if different
    personal_notes = []
    if notes_dir and os.path.isdir(notes_dir):
        personal_notes = scan_markdown_files(os.path.dirname(notes_dir), max_files_per_project=500)
        # Only keep notes from the notes dir
        personal_notes = [n for n in personal_notes if "notes" in n["path"].split(os.sep)[0].lower()]

    all_notes = note_nodes + personal_notes

    # 4. Build edges: project <-> notes, cross-project tech connections
    edges = []
    project_map = {p["name"]: p for p in project_nodes}

    # Connect notes to their parent project
    for note in all_notes:
        proj_name = note.get("project", "")
        if proj_name in project_map:
            edges.append({
                "source": note["id"],
                "target": project_map[proj_name]["id"],
                "label": "belongs_to",
                "type": "containment",
            })

    # Cross-project edges via shared tech
    for i, p1 in enumerate(project_nodes):
        for j, p2 in enumerate(project_nodes):
            if i >= j: continue
            shared_tech = set(p1["tech_stack"]) & set(p2["tech_stack"])
            shared_tags = set(p1["tags"]) & set(p2["tags"])
            if shared_tech or shared_tags:
                edges.append({
                    "source": p1["id"],
                    "target": p2["id"],
                    "label": ", ".join(list(shared_tech | shared_tags)[:3]),
                    "type": "shared_tech",
                })

    # 5. Note-to-note edges via wikilinks
    slug_map = {}
    for note in all_notes:
        slug = note["title"].lower().replace(" ", "-")
        slug_map[slug] = note
        slug_map[note["title"].lower()] = note

    for note in all_notes:
        for link_text in note.get("links", []):
            clean = link_text.split("|")[0].strip().lower()
            target = slug_map.get(clean) or slug_map.get(clean.replace(" ", "-"))
            if target and target["id"] != note["id"]:
                edges.append({
                    "source": note["id"],
                    "target": target["id"],
                    "label": link_text[:40],
                    "type": "wikilink",
                })

    # Deduplicate edges
    seen_edges = set()
    unique_edges = []
    for e in edges:
        key = (e["source"], e["target"], e["label"])
        if key not in seen_edges:
            seen_edges.add(key)
            unique_edges.append(e)

    # 6. Build node list for visualization
    all_nodes = []
    for p in project_nodes:
        all_nodes.append({
            "id": p["id"],
            "label": p["name"],
            "type": "project",
            "tags": p["tags"] + p["tech_stack"],
            "description": p.get("description", ""),
            "degree": 0,
            "project": p["name"],
        })

    for n in all_notes:
        all_nodes.append({
            "id": n["id"],
            "label": n["title"],
            "type": "note",
            "path": n["path"],
            "tags": n.get("tags", []),
            "project": n.get("project", ""),
            "summary": n.get("summary", "")[:200],
            "word_count": n.get("word_count", 0),
            "degree": 0,
        })

    # Compute degrees
    degree_map = defaultdict(int)
    for e in unique_edges:
        degree_map[e["source"]] += 1
        degree_map[e["target"]] += 1
    for node in all_nodes:
        node["degree"] = degree_map[node["id"]]

    # 7. Communities
    adjacency = defaultdict(set)
    for e in unique_edges:
        adjacency[e["source"]].add(e["target"])
        adjacency[e["target"]].add(e["source"])

    communities = label_propagation(all_nodes, adjacency)

    # 8. Stats
    orphans = [n["id"] for n in all_nodes if n["degree"] == 0]
    hubs = sorted(all_nodes, key=lambda n: n["degree"], reverse=True)[:20]

    tag_clusters = defaultdict(list)
    for node in all_nodes:
        for tag in node.get("tags", []):
            tag_clusters[tag].append(node["id"])
    tag_clusters = {k: v for k, v in tag_clusters.items() if len(v) > 1}

    return {
        "nodes": all_nodes,
        "edges": unique_edges,
        "adjacency": {k: list(v) for k, v in adjacency.items()},
        "communities": communities,
        "tag_clusters": tag_clusters,
        "orphans": orphans,
        "hubs": [{"id": h["id"], "label": h["label"], "degree": h["degree"]} for h in hubs],
        "stats": {
            "total_notes": len(all_nodes),
            "total_edges": len(unique_edges),
            "total_projects": len(project_nodes),
            "total_markdown_files": len(all_notes),
            "total_tags": len(tag_clusters),
            "orphan_count": len(orphans),
            "generated": __import__('datetime').datetime.now().isoformat(),
        },
    }


def label_propagation(nodes: list, adjacency: dict, max_iter: int = 15) -> dict:
    labels = {n["id"]: i for i, n in enumerate(nodes)}
    for _ in range(max_iter):
        changed = False
        for n in nodes:
            nid = n["id"]
            neighbors = adjacency.get(nid, set())
            if not neighbors:
                continue
            neighbor_labels = [labels.get(nb, 0) for nb in neighbors]
            most_common = max(set(neighbor_labels), key=neighbor_labels.count)
            if labels[nid] != most_common:
                labels[nid] = most_common
                changed = True
        if not changed:
            break
    unique_labels = list(set(labels.values()))
    remap = {old: new for new, old in enumerate(unique_labels)}
    return {nid: remap[lbl] for nid, lbl in labels.items()}


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "../"
    out = sys.argv[2] if len(sys.argv) > 2 else "../viz/graph-data.json"

    print(f"Indexing all projects under: {root}")
    graph = build_full_graph(root, notes_dir=None)

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")

    s = graph["stats"]
    print(f"\n[*] Knowledge Graph Complete")
    print(f"    Projects: {s['total_projects']} | Files indexed: {s['total_markdown_files']} | Total nodes: {s['total_notes']}")
    print(f"    Edges: {s['total_edges']} | Tags: {s['total_tags']} | Orphans: {s['orphan_count']}")
    print(f"    -> {out}")
