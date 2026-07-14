---
title: Graph Visualization Techniques
created: 2026-06-29 12:00
updated: 2026-06-29 12:00
tags: [reference, visualization, three-js]
---

# Graph Visualization Techniques

## Force-Directed Layout

Nodes repel each other; edges act as springs. The system settles into a layout
where connected nodes cluster and unrelated nodes drift apart.

- **Repulsion** — inverse-square force between all node pairs
- **Attraction** — spring force along edges
- **Damping** — velocity decay so the layout converges

## Rendering at Scale

- Instanced meshes for nodes
- Line segments in a single buffer for edges
- Bloom post-processing for the neon look

## Depth Cues in 3D

Size attenuation, fog, and glow intensity all help the eye judge distance —
critical in AR where the graph shares space with the real world.

## Links
- [[Knowledge Graph Theory]]
- [[AR Interface Design]]
