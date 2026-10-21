---
title: One line, e.g. "DXVK fixes CPU-bound stutter in <game>"
game: Game or project type, e.g. "Roblox experience"
engine: Engine and version
kind: shipped
hardware: CPU, GPU, RAM, OS
status: verified
date: 2026-01-31
---

## Complaint and target
What was slow, where, and the goal.

## Baseline
`uo compare` / profiler numbers, the test scene, how many runs.

## Bottleneck
What the measurements showed (GPU / one thread / shader compile / streaming / GC / network / memory).

## What worked
Each change: exact file, key or code pattern, the numbers, the trade-off, how to undo it.

## What didn't
Changes that were measured and reverted, with numbers.

## Gotchas
1. Symptom -> cause -> fix.
