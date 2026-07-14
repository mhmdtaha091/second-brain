---
title: Hand Gesture Recognition
created: 2026-06-29 12:00
updated: 2026-06-29 12:00
tags: [learning, computer-vision, mediapipe]
---

# Hand Gesture Recognition

Notes on building robust gesture control from webcam hand landmarks.

## The Jitter Problem

Raw landmark positions are noisy. Two techniques stabilize them:

- **EMA smoothing** — exponential moving average over landmark positions
- **Hysteresis state machine** — a gesture must persist for several frames
  before it activates, and several more before it releases

## Gesture Vocabulary

| Gesture | Detection | Action |
|---------|-----------|--------|
| Pinch | thumb–index tips close, other fingers extended | zoom / select |
| Fist | all four fingers curled (joint angles) | grab and rotate |
| Peace | index + middle extended, ring + pinky curled | overview |

## Lessons Learned

- Detect finger curl from joint angles, not tip distance — more robust across hand sizes
- Hard-reset gesture state when the hand leaves the frame to avoid phantom gestures
- Throttle inference and share one render loop to keep AR smooth

## Links
- [[AR Interface Design]]
- [[Second Brain System]]
