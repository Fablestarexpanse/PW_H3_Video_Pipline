---
title: "Fablestar Expanse - Production Bible"
type: production-bible
format: show
world: Fablestar Expanse
status: in development — GATE B pending on S01E01
created: 2026-08-11
tags: [movie-maker, production, fablestar-expanse, show]
---

# Fablestar Expanse — Production Bible

**Format.** Animated episodic series. Units are episodes.
**World.** [[Fablestar Expanse]] — world folder is the source of truth; this file is
production-owned.
**Status.** S01E01 cold open at draft v2. Nothing plated. GATE B not passed.

---

## What the show is

A man with thirty-one glyphs, who cannot say why he keeps going back, spends four days inside a
dead god's memory palace to finish a thirty-second one — and comes up to find that the only people
who ever stood beside him are dead or on the floor, and that he is now property.

**The engine:** *what does the thirty-second glyph do?* He knows. He has known for twenty years. He
has never been able to say why he wants it. Do not answer it in season one's front half.

## The two-thread grammar

The pilot cold open establishes a rule the show should keep:

| | THREAD A — inside | THREAD B — outside |
|---|---|---|
| Where | [[The Virtual Labyrinth]] | [[Bracken]], and later wherever they take him |
| Light | Warm amber, the only saturated colour in frame | Cold blue-white worklight, sick green instrument glow |
| Camera | Locked. Extreme wide. Absolutely still. | Handheld. Close. Never settled. |
| Scale | He never fills the frame | Nothing is wider than a room |
| Beauty | The one beautiful place | Nothing here is beautiful and nothing is warm |

**The threads never share a lens.** Every time they do, it costs something. In the pilot it happens
exactly once — four seconds of amber on the skin behind his left ear, in a room that has had no
warm light in it at all.

## Cast

| Character | Sheet | Baseline | Status |
|---|---|---|---|
| **Lan** | [[Lan]] | `700034` ✅ | LoRA `Krea2_Character_Lan007_v1` @ 0.80 |
| **Mira** | [[Mira]] | `700045` ✅ | Aged to fifties — beat-level note, **no re-baseline** |
| **Echo** | [[Echo]] | `700053` ✅ | Not in the cold open. Enters at the top of Act One. |
| **Kess** | [[Kess]] | ❌ | Turnaround sheet required |
| **Dov** | [[Dov]] | ❌ | Turnaround sheet required — include a prone/floor pose |
| **The Team Lead** | [[The Team Lead]] | ❌ | Turnaround sheet — one sheet covers all six operators |
| **The Medic** | [[The Medic]] | ❌ | Turnaround sheet — visor **up**, all three views |
| **The tank** | [[The Tank (Bracken)]] | ❌ | **Prop** turnaround sheet, no background |

**Design law — faceless is a choice, not a shortcut.** Nobody in the operator unit is a person yet.
The Medic is the only exception, and he argues twice and loses twice. The moment another visor
comes up, the show has spent something.

## Continuity threads open

1. **What the thirty-second glyph does.** The spine. Unanswered.
2. **Who sent the operators.** No insignia, no callsign, no name. Do not answer before the back
   half of the season.
3. **[[Kess]] is still zip-tied to a pipe.** Must be picked up in the first scene after the titles.
4. **[[Mira]]'s memorial log** is on the floor, open, face-down, stepped on, and still blank. She
   has not written [[Dov]]'s name. When she does, it should cost a scene.
5. **[[Lan]] knows the wreckage in the ring is human, and old** — one fact, no proof, twenty years
   of carrying it alone ([[Lan]] § *Clarification 2026-08-04*). He may imply the agreed story is
   wrong. He never explains how he knows. One line per act should stop just short.

## Routing — pinned

Per **R-027** / **R-029**. Do not cross these.

| Job | Workflow |
|---|---|
| ALL image work — plates, characters, props, locations, turnaround sheets | `PW_Krea2_VideoPrep_WF_V1` |
| Standard clips, 12–15s beats | `PW_video_minimax_h3_r2v_V1` |
| Long-form 1 min+ | `tnew` — never for single beats, **not production-ready as installed** |

**Style stack — LOCKED, never change it:**

```
<lora:SaintFame_Krea2_V2:0.60> <lora:FruityKicks_Krea2_V1.0:0.50> <lora:Rusted_Horizons_Krea2_V1.0:1.00>
```

**+ Lan, where he is a readable figure:**

```
...same... <lora:Krea2_Character_Lan007_v1:0.80>
```

`1344x768` · 11 steps · cfg 1.0 · euler/simple · one seed drives everything · CR-Prompts batch
mode. Krea-2 negatives go through **NegPip** as weights, never as prompt text (**R-022**) —
`(backpack:-1.4)`, removal range −1.2…−1.5, past −1.8 backs go hollow.

**File prefixes (R-024, separate at write time):**
`MovieMaker/Fablestar Expanse/S01E01/Plates/beatNN` · `MovieMaker/Fablestar Expanse/S01E01/Clips/beatNN`

## Style spines

**THREAD A — inside.**

```
illustration, high-contrast inked comic art, heavy deep blacks and rust-oxide midtones, warm
amber emissive light as the only saturated colour in frame, hard-edged geometric shadow shapes,
limited palette, grainy print finish, no gloss, no bloom, no lens flare
```

**THREAD B — outside.**

```
illustration, high-contrast inked comic art, heavy deep blacks, harsh cold blue-white worklight
and sick green instrument glow, a desaturated palette of raw concrete, bare steel and dirty
white, hard-edged geometric shadow shapes, limited palette, grainy print finish, no gloss, no
bloom, no lens flare
```

> Write the style bible from renders, not imagination. These spines are inherited from the prior
> production and are **unproven on this board** — expect to revise after the first plate batch.

## GATE D arithmetic — S01E01 cold open

Twelve beats ≈ seven to nine minutes of screen ≈ **35–42 clips** plus plates.

| Work | Cost |
|---|---|
| ~40 plates @ ~80s | **~55 min** |
| ~40 clips @ ~18 min | **~12 hours** |

Cost is superlinear in clip length (**R-021**) — do not extrapolate the 15.08s dialogue beats from
the 12.96s measurement. Measure at shipping length.

**Recommendation: two boards, not one.** Prove Thread A first — five beats, one character, cheaper,
and it is where FL2VA chaining (plate N first frame → plate N+1 last frame) earns its keep, because
A1→A2→A3 is a man walking continuously through one space.

## Blocked

- Four turnaround sheets do not exist ([[Kess]], [[Dov]], [[The Team Lead]], [[The Medic]]) plus
  one prop sheet ([[The Tank (Bracken)]]). One render each, then stop (**R-018**).
- [[Mira]]'s canon revision to her fifties is **pending Ronan's ratification at GATE A**.
- [[Bracken]] is a new world-level location, **pending GATE A**.
- Nothing plates until GATE B passes on the cold open.

## Episodes

| Episode | Status |
|---|---|
| [[Fablestar Expanse S01E01 - Thirty-Two]] | Cold open at draft v2. Act One not written. |


---

# ASSET STATUS — 2026-08-11

All sheets: `PW_Krea2_VideoPrep_WF_V1` · `1344x768` · 11 steps · cfg 1.0 · euler/simple · locked
style stack (R-029) · ~90 s each. Every approved sheet is stored twice — in the world
`Fablestar Expanse/Assets/<Name>/` and in `Reference Sheets/` here.

| Asset | Seed | Status |
|---|---|---|
| [[Lan]] | `800031` | ✅ approved — **hair and scar unresolved after 5 attempts**, see his sheet |
| [[Mira]] | `800042` | ✅ approved, clean |
| [[Echo]] | `800053` | ✅ approved, first attempt, clean |
| [[Kess]] | `800060` | ✅ approved, first attempt, clean |
| [[Dov]] | `800061` | ✅ approved — **wedding band wrong**, Klein edit pending |
| [[The Team Lead]] | `800062` | ✅ approved — **colour drift**, decision pending |
| [[The Medic]] | `800063` | ✅ approved — **orange visor**, decision pending |
| [[The Tank (Bracken)]] | — | ❌ **not rendered.** Prop turnaround still needed |

**All old single-front baselines for Lan, Mira and Echo are deleted from the vault** on Ronan's
instruction. `700034` is gone, so `Krea2_Character_Lan007_v1` no longer has its training source on
disk.

## Method rules earned this session — do not relearn these

1. **To remove something, describe what occupies that space instead**, pointing at something already
   in the frame. *"The same clean unbroken skin as the backs of her hands"* cleared [[Mira]]'s
   forearms after a negation and a NegPip weight both failed. Worked again on [[Kess]] and [[Dov]]
   first time.
   **But anchor to something the model has no reason to change.** *"The same grey as his beard"*
   moved [[Lan]]'s beard instead of his hair — an equality can be satisfied from either end.
2. **Blank faces need a real-object simile.** Echo's *"bare and unbroken like a frosted lamp bulb"*
   and the Team Lead's *"the plain blank surface of a motorcycle visor"*. Never "no face",
   "featureless", "no eyes" — those are absences and cfg 1.0 ignores them.
3. **The specifics block must not contain a pose.** [[The Medic]]'s canon crouch overrode the
   template's "standing upright" and produced three crouching figures. Habitual posture is
   beat-level. Template now hardened to *"standing upright at full height on both legs with the
   knees straight… arms hanging down at the sides."*
4. **Klein is for discrete hard-edged objects, not large soft regions.** It removed a glowing emblem
   cleanly and failed twice on hair, degrading the line work and tattoos each pass because it
   carries none of the Krea-2 LoRAs.
5. **Set the resolution before blaming the prompt.** At `3264x1836` a turnaround took ~7 minutes and
   drew six figures; at `1344x768`, ~90 s and exactly three.

## Open decisions

- **Operator palette.** Written as uniformly matte grey; rendered blue-grey with sage, bone and tan.
  Unmarked held; monochrome did not. Accept, or Klein-flatten to grey?
- **The Medic's orange visor** — same call, same pass.
- **[[Dov]]'s wedding band** — Klein edit, left ring finger, plain band.
- **[[Lan]]'s hair** — accept blue-black as canon, or keep trying?
