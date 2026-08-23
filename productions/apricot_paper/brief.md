---
status: draft
---
# Apricot Paper Story — Brief

One page. Five decisions. G1 refuses while any is blank.

| Decision | Value |
|---|---|
| Runtime (s) | ~90 s — 7 beats on the 17k+5 grid: 6 × 311 f + 1 × 362 f = 2228 f = 92.8 s (before ~1 s head trims) |
| Aspect | 16:9 — 1344×768, H3-native; every still and clip at this size |
| Audio source | none for now — clips render with H3's native audio muted in the cut; score/VO can be laid over the picture later (identity.AUDIO stays empty) |
| Cast count | 3 recurring named characters, each with an approved turnaround sheet before any clip |
| One-off vs format | show, but the pilot stands alone — a complete 90 s story that sets the world, not a cliffhanger |

## Premise
A Redwall-shaped story for adults: the mice of a sandstone abbey above autumn woods, where the feasts are real
and so are the wounds. A scarred veteran keeps the gate; two others — to be cast at G2 — carry the pilot's
turn. Ninety seconds, one location complex (gate, great kitchen, the hill), hand-drawn on apricot paper: ink
line, watercolour wash, candle and hearth light, one saturated accent per frame.

## What this fixes downstream
- `beats.csv`: 7 beats, frames as above; `cut_time` is the running total.
- `identity.ASPECT = (1344, 768)`; `AUDIO = {}`.
- Canon (G2): 3 `characters/*.md`, ≤2 adjectives per axis; locations: gate, great kitchen, hill-wide.
- No voice locks (no dialogue). If dialogue is added later, that is a brief change and a new G1.
