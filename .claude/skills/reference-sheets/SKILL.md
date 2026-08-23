---
name: reference-sheets
description: Render, measure and approve reference images (character/prop turnaround sheets, location templates, master wides, tight crops) for the REFS stage (G4). Use when writing prompts/refs.lines, running refqc.py, or filling identity CAST/LOCATIONS.
---

# Reference sheets — the REFS stage (G4)

A prompt fragment will not hold a character (ten plates, identical fragment: haircut and scar
drifted, apparent age varied ~20 years). Identity is held by an **approved sheet** riding into every
clip as `<Picture N>`. One approved sheet per asset, then stop.

## The order

1. Write one prompt per asset into `<unit>/prompts/refs.lines` (escaped, one line each) — start from
   the defaults below **verbatim**, then append the specifics.
2. Queue 2–3 seeds per asset as `mm_image_v1` rows (`render.py`), 1344×768 for sheets and plates
   (a "three views" prompt holds at 1344×768 and draws six figures at 3264 wide). Land with
   `landed.py`; candidates arrive in `F:\MovieMaker\<slug>\refs\candidates\`.
3. Measure every candidate and record it:
   `python tools/refqc.py <png> --kind sheet --figures 3 --record <slug>` ·
   `--kind plate [--block LO HI]` (photoreal) · `--kind plate-illustrated` (ink/watercolour/paper-grain style: waives the white limit — rain streaks, candle glow and paper grain legitimately run high) · `--kind crop`. Present the PNGs with their numbers **and stop**.
   Never queue a clip "while Ronan looks".
4. Ronan picks or rejects the set ("neither, go X" is expected). On a pick: copy to
   `productions/<slug>/refs/<key>_APPROVED_<seed>.png` (committed), set the manifest row to
   `status: approved`, fill `identity.CAST/LOCATIONS[key] = {sheet, seed, slot}`. Rejects are renamed
   `*__rej_<reason>.png` on the drive — never deleted. `contract.py` must hold.
5. A proof clip on candidates is allowed once per production (`render.py --proof`); a board is not.

## What refqc measures and why (a reference teaches everything in it — LAWS §8)

| Metric | Why | Rule |
|---|---|---|
| mean luminance | a work-lit plate taught brightness: slot came back at 89 against a film at 40–60 | `--block LO HI` = the block it feeds |
| % pixels > 235 | a 26 % near-white grill crop cut clips to a white studio void | **< 1.5 % for crops and plates**; sheets are on white by design (`--kind sheet` waives it) |
| % pixels < 20 | how much of the frame is genuinely black | high for a night interior |
| figure count | "exactly three" did not hold at 3264 wide | `--figures 3` on sheets (known failure: views whose hair overlaps on a 768-wide portrait sheet read as 1 — count by eye) |

## Default prompts

**Character turnaround** (swap man/woman; then append the specifics — size/height · age · body ·
hair colour and style · eyes · distinguishing marks and jewellery · wardrobe colours/materials/
condition; one or two cues per trait, never three):

> A character turnaround reference sheet populated by exactly one figure, the same single man,
> repeated in three full-body drawings arranged in one centered horizontal row with clear gaps
> between them: front view, then side view, then back view. Each figure sits entirely within its
> own margin, wholly clear of every edge of the image. A seamless plain white studio backdrop
> fills the entire background in a flat, even, colour-neutral wash of light, uniform and
> shadowless across the whole sheet. All three figures are exactly the same height and build,
> standing upright in a neutral relaxed pose, drawn small enough that each complete body fits
> inside the frame with empty space above every head and a clear strip of perfectly clean bare
> white floor below every pair of feet; feet are fully visible, resting well above the bottom edge.

(Rewritten 2026-08-23 — LAWS §1/§4: the original phrased "no other figures", "no partial figures
touching any edge" and "no shadows, no coloured light" as negatives and failed preflight's
stale_neg check the first time it was used end to end. Same content, stated positively.)

**Prop turnaround:** same shape, "exactly three drawings of the same single object and nothing
else … floating on clean white with no surface". Then size relative to a hand, materials, colours,
wear, moving parts — identical wording every time the prop is re-rendered.

**Locations:** devoid of people (ambient fill only when the place *is* a crowd), lit **as the film is
lit**, not for legibility. Conditioning only — it never appears in the film; it needs to be accurate,
not beautiful. In the clip prompt say exactly what is taken from it and what stays in the photograph.

## Two things learned the hard way

- **An accessory drops out of one view** (a cap fine in side/back, gone in front — three seeds running).
  Name the view and state the item is identical across all three: *"the cap and its brim are worn and
  clearly visible in the front view exactly as they are in the side view and the back view, present
  and identical in all three drawings."* Fixed on the next seed.
- **Removing an established accessory by negation fails** (*"no glasses … of any kind"* rendered the
  glasses in two views). Positive equality works on the next seed: *"her eyes are wide open and plainly
  visible in the front view, the side view and the back view … her loose hair the only thing near her
  face in every view."*

## NegPip (mm_image_v1, the one sanctioned negative edit point)

Stock line for the locked photoreal style stack: `(backpack:-1.4), (antenna:-1.2), (shoulder straps:-1.1),
(belt pouches:-0.8), (debris on the ground:-1.2), (clutter on the floor:-1.1), (rocks and rubble at their
feet:-1.0), (paint splatter:-0.9)`. Weights −1.2…−1.5 remove; past −1.8 backs go hollow. The style stack's
blue-black spiked hair survived −1.5 — that needs a different lever, not more weight. Set `negpip: ""` on
the job row for a production with no style stack.
