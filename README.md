# 🧠 Second Brain

> Your knowledge, visualized. Local-first. AR-ready. 100% free.

![Version](https://img.shields.io/badge/version-1.0.0-00f0ff)
![License](https://img.shields.io/badge/license-MIT-b44dff)
![Platform](https://img.shields.io/badge/platform-local--first-ff3d7f)

---

## What is this?

A **personal knowledge management system** that stores your notes as plain markdown, builds a knowledge graph from your `[[wikilinks]]`, and lets you **explore it in 3D/AR** with hand gestures. Think Obsidian meets Minority Report — but everything runs on your machine, nothing touches the cloud, and it's completely free.

### Core Features

| Feature | Description |
|---------|-------------|
| 📝 **Markdown Notes** | Write in any editor. YAML frontmatter + `[[wikilinks]]` |
| 🕸️ **Knowledge Graph** | Auto-built from links. Communities, hubs, orphans detected |
| 🌌 **3D Visualization** | Three.js force-directed graph. Cyberpunk neon aesthetic |
| 🔮 **AR Mode** | WebXR. Explore your knowledge floating in your room |
| ✋ **Hand Gestures** | MediaPipe hand tracking. Grab, pinch, swipe to navigate |
| 🔍 **Full-Text Search** | Instant search across all notes |
| 📊 **Stats & Insights** | Hubs, orphans, tag clusters, community detection |
| 🔒 **100% Local** | Your data never leaves your machine. No cloud, no telemetry |
| 🗃️ **Git Versioned** | Every change tracked. Nothing is ever lost |

---

## Quick Start

### Prerequisites
- **Python 3.10+** (for the engine, CLI, and server)
- **A modern browser** (Chrome/Edge for best AR + hand tracking support)
- **Git** (optional, for versioning)

### Install & Run

```bash
# 1. Clone or navigate to the project
cd second-brain

# 2. Install Python deps (only PyYAML needed)
pip install -r requirements.txt

# 3. Launch!
python cli/brain.py serve
```

Your browser opens to `http://localhost:8420` — you'll see your knowledge graph in 3D.

---

## Usage

### CLI Commands

```bash
# Create a note
python cli/brain.py note "My New Idea" --tag idea,project

# Link two notes together
python cli/brain.py link "My New Idea" "Second Brain System"

# Full-text search
python cli/brain.py search "knowledge graph"

# Today's daily note
python cli/brain.py daily

# Show stats
python cli/brain.py stats

# List all tags
python cli/brain.py tags

# Find unlinked notes
python cli/brain.py orphans

# Regenerate graph JSON
python cli/brain.py graph
```

### 3D Visualization Controls

| Input | Action |
|-------|--------|
| 🖱️ **Drag** | Rotate view |
| 🖱️ **Scroll** | Zoom in/out |
| 🖱️ **Click node** | Open detail panel |
| ⌨️ **F** | Fit all nodes in view |
| ⌨️ **S** | Focus search bar |
| ⌨️ **T** | Toggle tag color mode |
| ⌨️ **R** | Toggle auto-rotate |
| ⌨️ **ESC** | Close detail panel |

### Hand Gestures (click "✋ Hands" in the UI)

| Gesture | Action |
|---------|--------|
| ✌️ **Peace sign** | Zoom out |
| 🤏 **Pinch** | Zoom in / select |
| ✊ **Grab** | Rotate graph |

### AR Mode (click "🔮 AR")

Requires a WebXR-compatible browser and device. On your phone, the graph appears in your real space. Walk around it. Grab it with your hands.

---

## How It Works

```
notes/                  ← You write markdown here
  ├── daily/
  ├── projects/
  ├── learning/
  └── references/

graph/engine.py         ← Parses notes → builds graph → detects communities
viz/graph-data.json     ← Auto-generated graph for the frontend
viz/index.html          ← 3D/AR visualization (Three.js + WebXR + MediaPipe)
server.py               ← Local HTTP server + REST API
cli/brain.py            ← CLI for creating, linking, searching
```

**The pipeline:**
1. You write a note with `[[wikilinks]]` → any text editor works
2. `graph/engine.py` parses all `.md` files, extracts links/tags/frontmatter
3. Builds a bidirectional graph with community detection
4. Exports JSON to `viz/graph-data.json`
5. `viz/index.html` renders it in 3D with Three.js
6. WebXR + MediaPipe enable AR + hand control

---

## Architecture Decisions

| Decision | Why |
|----------|-----|
| **Markdown, not database** | Future-proof, git-friendly, any editor works |
| **Local HTTP server** | No Electron bloat. Browser is the best renderer |
| **Three.js, not Unity** | Free, web-native, no install, WebXR built-in |
| **MediaPipe, not Leap Motion** | Free, runs in browser, no hardware needed |
| **YAML frontmatter** | Standard (Obsidian/Zettlr/Hugo compatible) |
| **No cloud** | Privacy. Speed. Control. Your data, your rules |

---

## Extending

### Add a custom visualization theme
Edit `viz/index.html` — the CSS variables at the top control the entire look:
```css
--accent: #00f0ff;    /* Cyan → change for different vibe */
--accent2: #b44dff;   /* Purple */
--accent3: #ff3d7f;   /* Pink */
```

### Connect to a private GitHub repo for backup
```bash
cd notes/
git init
git remote add origin git@github.com:you/your-second-brain.git
git add -A && git commit -m "Brain snapshot"
git push
```

### Encrypt your notes
Edit `config.yaml`:
```yaml
security:
  encrypt_notes: true
```

---

## FAQ

**Is this really free?** Yes. Every component is open-source and free. Three.js (MIT), MediaPipe (Apache 2.0), Python (PSF). No paid tiers, no subscriptions.

**Can I use this without AR?** Absolutely. The 3D view works great on desktop with mouse/keyboard.

**What if I delete a note by accident?** Use git to recover: `git checkout -- path/to/note.md`. Or check the `.trash/` folder.

**Does this work offline?** Yes. Once the page loads, everything runs locally. The MediaPipe model is cached after first load.

**Can I import my Obsidian vault?** Yes! Just copy your markdown files into `notes/`. The `[[wikilinks]]` format is identical.

---

## Roadmap

- [ ] Note encryption at rest (AES-256)
- [ ] AI-powered link suggestions (local LLM)
- [ ] Timeline view (chronological graph)
- [ ] Mobile PWA for quick capture
- [ ] Voice notes → auto-transcription
- [ ] Multi-vault support
- [ ] Plugin system

---

*Built by [Muhammad Taha Khan](https://github.com/mhmdtaha091)*
