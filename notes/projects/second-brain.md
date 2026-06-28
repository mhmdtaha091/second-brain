---
title: Second Brain System
created: 2026-06-29 12:00
updated: 2026-06-29 12:00
tags: [project, second-brain, knowledge-management, AR]
---

# Second Brain System

A local-first knowledge management system with AR visualization.

## Core Principles

- **100% Local** — All data stored on your machine, never leaves
- **Git-backed** — Every change is versioned, nothing is ever lost
- **AR-Ready** — Visualize your knowledge in 3D space
- **Hand Control** — Navigate with gestures, Minority Report style
- **Markdown Native** — Plain text, future-proof, any editor works

## Architecture

The system has four layers:
1. **Notes** — Markdown files with YAML frontmatter and `[[wikilinks]]`
2. **Graph Engine** — Parses notes, builds a knowledge graph, detects communities
3. **Visualization** — Three.js 3D force-directed graph with AR mode
4. **CLI** — Command-line interface for quick operations

## Technology Stack

- Python (graph engine, CLI, server)
- Three.js (3D visualization)
- WebXR (AR mode)
- MediaPipe (hand gesture recognition)
- Git (version control)

## Links
- [[Knowledge Graph Theory]]
- [[AR Interface Design]]
- [[Markdown Best Practices]]
