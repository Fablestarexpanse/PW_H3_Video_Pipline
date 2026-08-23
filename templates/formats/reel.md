# Format — the reel ("build a [theme] outfit with me")

Ported from the Wren Production Bible (Format, Transitions, Piece-by-piece build, Performance
style) and LAWS Appendix B. Measured on two eight-clip and one eleven-clip build; zero re-rolls
on the last.

## What it is
Not a cinematic short: a lookbook transformation reel. One recurring character, one locked
location, vertical 9:16 (768×1344), "as if filmed on a phone held stationary at chest height,
24–28 mm equivalent". The camera never moves; she moves and plays to the lens. The fixed axis is
what makes garment changes read as polished. Independent short Ref2VA generations — 124 f (5.2 s)
beats, a 226 f (9.4 s) finale — hard-cut together; no chain, no FL2VA. Identity holds across 8–11
independent generations from sheets alone, no LoRA.

## References per beat (identity slots)
- `<Picture 1>` = **the look for this beat**: the before-state sheet for beat 1, the theme's
  master wide for every later beat (the approved completed-look full-body still on the set).
- `<Picture 2>` = the character turnaround sheet, every beat.
- Every prompt restates body, hair, skin (porcelain-pale, freckled, "stays cool and pale in the
  warm room light"), septum ring, choker and the set — per shot, the way a sheet does per panel.
  **Double-anchor the body** (top of prompt + inside the outfit paragraph) whenever the skin block is
  present; they compete (LAWS §13).

## beats.csv modes
- `ref2va-master` — a full-body beat that opens on the master wide exactly as framed. Frame zero
  IS `<Picture 1>`; `retention_analysis` must say so; `clipqc --expect-master` refuses a clip that
  does not open on it (Dark Muse: 5 of 10 opened at +0.999).
- `ref2va` — a seated shot, a detail insert, an ECU: its own framing, so frame zero must be
  described positively (LAWS §1). The one beat that skipped this opened on a fuller body than the
  rest of the clip.
- `state_changes: occlusion-tail:12` — the beat ends in a scripted occlusion to black; clipqc
  exempts those frames.

## The three shot types (alternate them — the repetition is the grammar)
1. **Full-body fashion pose** — the master-wide composition; slow controlled movement: turn, hip
   shift, hands on waist, look over the shoulder.
2. **Extreme detail presentation** — she brings the object *into* the lens (jewellery, fabric, a
   hand, a belt) until it nearly fills the 9:16 frame and goes slightly soft; her face stays visible
   behind it. Foreground exaggeration is the point.
3. **Transformation / reveal** — the return to full-body, now in the next clothing state.

## Transitions — the occlusion is where the garment changes
H3 does not reliably transform a garment mid-generation. Build each state as its own clip and cut
at the most-occluded frame: hand/jewellery/fabric approaches the lens → frame mostly obscured → cut →
object moves away → new state revealed. Rotate: spin toward camera · fabric sweep across the lens ·
hand covering the lens · pendant held into the lens ("lens wipe") · walking very close · body passing
across frame · skirt thrown across the lens mid-spin · a garment tossed toward camera, landing after
the cut. Write the occlusion **concretely and positively**: *"the pendant fills the frame edge to
edge like a gold coin held to the lens"* (fixed 1 of 2 outright, improved the other). "Occlude and
cut" beats deliver; "occlude and hold" beats are still weaker — measured: one reached black, one
resolved back to a clear shot.

## Build order of a reel
Before-state hook (base layer, ≤3 s, framed as building, never undressing; adult only) → one garment
per beat in dressing order → accessories as ECU occlusions → full-outfit reveal → two movement beats
(hip circle / slit trail / look over shoulder; walk toward camera / hair flip) → close beauty shot
(smirk, eyebrow raise, smile) → finale: 3/4 turn, back view, approach, accessory lens-cover close.

## Performance, captions, music
She is playful and self-assured — she already knows the outfit works: subtle smirk, eyebrow raise,
direct unbroken eye contact, a small hip shift, checking herself over, then back to the lens. Action
carries the beat (pull the skirt into position, cinch the belt, throw the shawl, adjust hair, rotate
hips, walk in), never a static hold. Captions: elegant serif, all caps, centred, one short line per
beat. Music: `non_diegetic_music` carries it (mellow acoustic/world-folk; every cut on a beat); no VO,
no voice locks. Themes rotate on a dark-bohemian base: woodland witch, desert nomad, dark muse,
cottage fae, festival, cozy autumn, sea-witch.

## When a new reel is requested
Beat sheet (`beats.csv` + `slot_names.txt`), one still description per beat, one motion description
per beat (what she does, what enters frame, where the cut lands), caption text — then `preflight`.
Cost: ~10 min wall at 175 f measured; 124 f and 226 f points measure on the first clip (superlinear).
