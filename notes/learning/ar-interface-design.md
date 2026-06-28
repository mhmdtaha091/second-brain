---
title: AR Interface Design
created: 2026-06-29 12:00
updated: 2026-06-29 12:00
tags: [learning, AR, design, UX]
---

# AR Interface Design

Designing interfaces for augmented reality requires rethinking fundamental interaction paradigms. Screens become space; clicks become gestures.

## Design Principles

### Spatial First
Everything has a position in 3D space. Interfaces shouldn't be flat rectangles floating in front of you — they should occupy meaningful spatial positions.

### Gesture-Driven
- **Pinch** — Select, grab
- **Grab** — Move, rotate
- **Swipe** — Navigate, dismiss
- **Point** — Target, highlight

### Glanceable
AR interfaces must convey information at a glance. Depth, color, size, and motion encode meaning faster than text.

## Hand Tracking

MediaPipe provides 21 hand landmarks per hand, enabling:
- Pinch detection (thumb-index distance)
- Grab detection (finger-curl analysis)
- Pose estimation (orientation, pointing direction)

## Visual Language for Knowledge Graphs in AR

- **Node size** = importance / connectivity
- **Node color** = community / category
- **Edge thickness** = relationship strength
- **Edge glow** = recently accessed / active
- **Spatial clustering** = semantic similarity

## Links
- [[Second Brain System]]
- [[Knowledge Graph Theory]]
- [[Graph Visualization Techniques]]
