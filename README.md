# Second Brain

**Your knowledge as a living 3D graph — walk around it in AR, grab it with your bare hands.**

Second Brain turns a folder of plain markdown notes into an interactive knowledge graph: a Python engine parses `[[wikilinks]]`, detects communities and hubs, and a Three.js front-end renders the result as a neon force-directed graph you can explore in the browser — or drop into your room via WebXR and steer with MediaPipe hand tracking. Pinch to zoom, make a fist to grab and rotate, flash a peace sign to jump back to overview. No cloud, no accounts, no telemetry: everything runs and stays on your machine.

> **TODO:** hero GIF — 3D graph orbit + AR hand-grab clip (`docs/media/hero.gif`)

![Version](https://img.shields.io/badge/version-1.0.0-00f0ff)
![License](https://img.shields.io/badge/license-MIT-b44dff)
![Platform](https://img.shields.io/badge/platform-local--first-ff3d7f)

---

## Features

| Feature | Description |
|---------|-------------|
| **Markdown notes** | Plain files, YAML frontmatter, Obsidian-style `[[wikilinks]]` — any editor works |
| **Knowledge graph** | Auto-built from links: community detection, hubs, orphans, tag clusters |
| **3D visualization** | Three.js force-directed graph with bloom, instanced nodes, cyberpunk aesthetic |
| **AR mode** | WebXR — the graph floats in your real space on a compatible device |
| **Hand gestures** | MediaPipe hand tracking with EMA smoothing + a hysteresis state machine, so gestures don't jitter or misfire |
| **Workspace indexer** | Optional mode that maps an entire projects folder (READMEs, docs, tech stacks) into one graph |
| **CLI** | Create, link, and search notes from the terminal |
| **100% local** | Local HTTP server on `127.0.0.1`. Your notes never leave your machine |

---

## Quickstart

Prerequisites: Python 3.10+, a Chromium-based browser (best AR + hand-tracking support), a webcam for gestures.

```bash
git clone https://github.com/mhmdtaha091/second-brain.git
cd second-brain
pip install -r requirements.txt

# Build the demo graph from the bundled sample notes
python graph/engine.py examples/notes export viz/graph-data.json

# Serve the 3D visualization
python server.py
```

Your browser opens `http://localhost:8420` with a small demo graph (7 sample notes about knowledge graphs, AR design, and gesture recognition). Then:

- **Mouse:** drag to rotate, scroll to zoom, click a node for details
- **Keyboard:** `F` fit view · `S` search · `T` tag colors · `R` auto-rotate
- **Hands:** click **✋ Hands**, allow the webcam, and control the graph directly
- **AR:** click **🔮 AR** on a WebXR-capable device

### Hand gestures

| Gesture | Action |
|---------|--------|
| 🤏 Pinch + move hand | Zoom / scale the graph; twist wrist to rotate |
| ✊ Fist | Grab — rotate and pan the graph in space |
| ✌️ Peace sign | Snap back to overview |

> **TODO:** short clips of each gesture (`docs/media/gesture-pinch.gif`, `gesture-fist.gif`, `gesture-peace.gif`)

---

## Using your own notes

Point the graph engine at any folder of markdown files:

```bash
python graph/engine.py path/to/your/notes export viz/graph-data.json
python server.py
```

Notes are plain markdown with optional YAML frontmatter:

```markdown
---
title: My Note
tags: [idea, project]
---

# My Note

Connect ideas with [[Another Note]] — links become edges in the graph.
```

The CLI works against the local `notes/` directory (gitignored, so your personal notes are never committed):

```bash
python cli/brain.py note "My New Idea" --tag idea      # create a note
python cli/brain.py link "My New Idea" "Another Note"  # add a wikilink
python cli/brain.py search "knowledge graph"           # full-text search
python cli/brain.py daily                              # today's daily note
python cli/brain.py stats | tags | orphans             # graph insights
```

### Workspace indexer mode

`graph/project_indexer.py` can index a whole projects folder instead of a notes vault: it reads each project's README/manifests, infers the tech stack, scans markdown docs, and links projects that share technologies.

```bash
python graph/project_indexer.py path/to/your/projects viz/graph-data.json
```

> **Privacy note:** the server and CLI default to indexing the *parent* directory of this repo when no `viz/graph-data.json` exists. The generated `viz/graph-data.json` contains excerpts of whatever was indexed — it is gitignored for that reason. Build the graph from `examples/notes` (or your own vault) first if you don't want sibling folders scanned.

---

## Architecture

```
examples/notes/         Sample vault (demo content)
notes/                  Your personal vault (gitignored)

graph/
  engine.py             Markdown → graph: frontmatter, wikilinks, tags,
                        label-propagation communities, hubs, orphans
  project_indexer.py    Workspace mode: project identity, tech-stack
                        detection, cross-project edges

viz/
  index.html            Single-file front-end: Three.js force-directed
                        scene, WebXR AR session, MediaPipe HandLandmarker,
                        gesture state machine, search + detail panels
  graph-data.json       Generated graph (gitignored)

server.py               Local HTTP server + REST API (/api/graph, /api/search,
                        /api/tags, /api/refresh) on 127.0.0.1:8420
cli/brain.py            CLI entry point
```

**Pipeline:** markdown files → parse (frontmatter, `[[wikilinks]]`, `#tags`) → adjacency + degree metrics → label-propagation community detection → JSON export → Three.js renders nodes/edges with bloom → WebXR promotes the scene to AR → MediaPipe landmarks feed a smoothed gesture state machine that drives the camera and graph transform.

**Gesture engine details:** 21 landmarks per hand; finger state derived from joint angles (robust across hand sizes) rather than tip distances; EMA smoothing plus hysteresis thresholds prevent flicker between gestures; state hard-resets when the hand leaves the frame to avoid phantom grabs; MediaPipe inference is throttled and shares a unified render loop with Three.js to keep AR frame rates stable.

### Design decisions

| Decision | Why |
|----------|-----|
| Markdown, not a database | Future-proof, git-friendly, works with Obsidian/Zettlr vaults |
| Local HTTP server, no Electron | The browser is already the best 3D/AR renderer |
| Three.js + WebXR, not Unity | Web-native, no install, AR built in |
| MediaPipe, not depth hardware | Hand tracking from any webcam, runs in-browser |
| Zero dependencies beyond PyYAML | The whole engine is standard library + one parser |

---

## Status

**Working today:** graph engine, workspace indexer, 3D visualization, search, tag/community coloring, WebXR AR mode, pinch/fist/peace gesture control, CLI, local server.

**Honest limitations:**

- `config.yaml` is currently a placeholder — paths and ports are set at the top of the scripts, not read from it yet
- Note encryption is not implemented (the config flag is aspirational)
- Git versioning of notes is manual — `notes/` is a plain folder you can `git init` yourself
- AR mode depends on device WebXR support; desktop 3D works everywhere

**Roadmap:** wire up `config.yaml` · note encryption at rest · AI link suggestions (local LLM) · timeline view · mobile PWA capture · multi-vault support.

---

## FAQ

**Is this free?** Yes — Three.js (MIT), MediaPipe (Apache 2.0), Python (PSF). No services, no tiers.

**Can I use it without AR?** Absolutely — the desktop 3D view with mouse/keyboard is the primary mode.

**Can I import my Obsidian vault?** Yes. Point the engine at your vault folder — the `[[wikilink]]` format is identical.

**Does it work offline?** Yes, after first load (the MediaPipe model and Three.js modules are fetched from CDNs once, then cached).

**Where does my data go?** Nowhere. The server binds to `127.0.0.1` and there are no analytics or network calls with your note content.

---

*Built by [Muhammad Taha Khan](https://github.com/mhmdtaha091)*
