# LAWS — how the models actually behave

Laws of the **model**, not preferences about style. Every one was paid for in renders across
five productions and two genres. Structure of an H3 prompt comes from the `h3-prompt-writing`
skill; this file is what the skill cannot know. Read once per session. Each law names the
`preflight.py` check that enforces it, where one can.

---

## The one law

> **The model builds from what is present, not from what is absent.** A description is
> present. A prohibition is a description of the thing you don't want, plus a word.

Three faces: absence isn't buildable (*"no urinals"* rendered urinals) · vividness outranks
negation (a rich description with "never" attached loses) · presence cuts both ways (*"the
contact is never shown"* was obeyed exactly).

---

## 1 · The model fills vacuums; a prohibition is not a filling
Unspecified things get filled from priors, and the priors are dramatic.

| Vacuum | What filled it | What worked |
|---|---|---|
| Nothing for his hands in the first 4 s | bite at 1.9 s, two seeds | a task physically incompatible with the action |
| Frame zero not described | reference plate reproduced, corr **+0.97** | *"The first frame is already a medium shot of him at chest height…"* → **+0.03** |
| Her arms unassigned | around his neck — kill read as a kiss | *"her arms stay down"* |
| Only the attacker described | opponents stand and wait their turn | every body has a continuous action in every shot |

**Move:** before writing a prohibition, answer *what is it doing instead* and write that.
Pick business that leaves no residue (walking, holding a rail — not fluids, not food).
→ `preflight: frame_zero_positive`

## 2 · A vivid description outranks a prohibition attached to it
`SCALE STATE` ending "never by framing wide" was otherwise a list of things only visible from
far away; it beat three framing rules across six renders. Deleting it fixed three slots in one.

**Escalation ladder — climb in order, never skip:**
1. find the word already fighting you and delete it (*"holds her upright"* outvoted three sentences)
2. declare a winner out loud (*"…and it overrides every other instruction here"*)
3. delete the competing block entirely
4. change the shot design so the failure cannot happen (remove every cut; remove the camera's freedom)

Six renders were burned on rungs 1–2 before rung 3 worked first time.
→ `preflight: no_scale_state`

## 3 · "Not shown" is obeyed about the thing you want to see
A kill read as a touch for three versions because an earlier draft said *"the contact itself
is never shown."* Discretion written in one draft survives into drafts that no longer want it.
→ `preflight: discretion_clauses` — `never shown · out of view · hidden · not visible ·
off-screen · implied · we do not see`. Every hit is a decision, not a skim.

## 4 · Negatives work on objects, never on modes, camera positions or absences
| | Krea-2 stills | H3 motion |
|---|---|---|
| prompt-text negatives | do nothing at cfg 1.0 | work **if specific and about an object** |
| the real lever | NegPip weights `(backpack:-1.4)`, for standing style-stack taxes only | node negative input; positive statement of the mode you want |

*"Every frame is a frame of a music video inside a crowded club"* works where *"no studio
portraits"* does not. Standalone negative lists in combat clips were ignored; the same negatives
embedded as positives (*"hammer never touches the water"*, *"exactly ONE weapon"*) held.

**Absence by positive equality:** never *unlit / featureless / absent*. *"exactly as dark as
the ink of the linework around them"* · *"a smooth blank ovoid, bare and unbroken like a
frosted lamp bulb"* · *"plain bare skin from elbow to wrist, the same clean skin as the backs
of her hands."* Point at something already in frame.
→ `preflight: stale_negatives` (a `no X` carried from a previous look)

## 5 · Continuity is a timed STATE, not an event
Lives in `retention_analysis`. *"Clean in EVERY frame until 00:12.400. Blood appears at
00:12.400 and is present in every frame after. It REMAINS after the wipe, unchanged."* Landed
to the frame across six clips. The anti-tidying clause is load-bearing. Actions are states
too: start position, end position, monotonic direction. Injuries in a fight are states: named,
and restated in every later shot.

## 6 · If an action needs a piece of the world, the framing must contain it
A collapse failed as a medium two-shot because the floor was not in frame. Ask of every
action: what must be visible for this to be physically possible?

## 7 · Composite meaning comes from orientation, not parts
Predation and romance share a body language; every clause was obeyed and the composite was
still an embrace. Orientation stated positively (behind, over the left shoulder, chest to
back) · a named side, repeated · every limb placed · a whole-frame test the model can apply
(*"if a frame looks like two people kissing, it is wrong"*). Lock screen direction in fights
(A always hero's left, B right) and say eyelines match across cuts.

## 8 · A reference teaches everything in it
| Fault in the reference | What it cost |
|---|---|
| grill macro 26 % near-white | clips cut to white studio void mid-clip |
| location plate bright and work-lit | block came back at luminance 89 against a film at 40–60 |
| location plate correctly empty | clips opened on the empty room, corr +0.97 |

State in `subject_definitions` what is and is not taken (*"NOT its emptiness, NOT its framing,
NOT its camera position, NOT its lighting"*), **and** describe frame zero positively — the
exclusion alone stops citation, not copying. Measure every candidate (`refqc.py`): mean
luminance, % >235 (< 1.5 %), % <20, medium.
→ `preflight: refs_approved`, `clipqc: ref_leak`

## 9 · Two instructions competing for one variable will fight — name the variable
Scale vs legibility both want camera distance: carry scale **above and behind** the subject
(ceiling, trusses, crowd receding past his shoulders), never by pulling back. A bite vs lip-sync
both want the mouth: give `MOUTH STATE` an exemption window and schedule them in time.
**Size by in-frame anchor** beats fractions (*"no taller in frame than the rubble heaped at
their bases"*); fractions only for legibility floors. Point the camera where the words are.

## 10 · Rule density itself collapses a clip to one locked wide
Found independently on combat clips with **no competing block at all**: a beat sheet too dense
makes the model take the composition that satisfies the most constraints at once — a wide.
**Counter-move: write coverage positively** — alternate wide → tight → tight → wide, lens and
DOF per shot, a minimum number of inserts, one low angle. Past the template's block count,
the next fix is cutting a rule, not adding one.
→ `preflight: block_count`

## 11 · Say the important thing three times, in three sections
A locked camera is what H3 most reliably ignores; state the lock in `summary`,
`retention_analysis` and the shot description. Repetition across sections survives the
attention budget; repetition inside one paragraph is padding.
→ `preflight: lock_stated_thrice` (advisory)

## 12 · Adjectives compound; name the noun before the strangeness
"Lean" + "stubble" + "tired" → strung out; three ageing cues → seventy. One or two per axis.
The style stack draws its own defaults (every emissive light warm amber; blue spiked hair;
soldiers with emblems) — anonymity cannot be asked for, and a description that holds at
full-figure scale can fail at portrait scale. Muted colour names drift (*khaki* → olive,
three times); loud plain names hold (*flamingo pink*). Carried props belong in beats, never in
the character fragment.
→ `canon: adjective_count`

## 13 · Prompt blocks compete for weight
On Wren, every render carrying both a skin/freckle block and the body-shape block needed
iteration to hold the body; without the skin block it held first time. **Double-anchor** the
thing that must hold — once at the top, once inside the paragraph it competes with — rather
than intensifying it once.

## 14 · Measure it, and give every instrument a control
A timing grid scored worse than 500 randomly placed grids and shipped. A chunked forced
aligner stretches text to fill its window. Whole-frame means are blind to a mouth (1 % of
frame). Confirm frame counts with `ffprobe`; the widget lies (`13.0` → 328 frames). Sweep the
whole cut, not the clip you just made. See `tools/clipqc.py --selftest`.

---

## Fault → move

| Symptom | Cause | Move |
|---|---|---|
| clip opens on the reference plate | frame zero undescribed | describe frame zero positively **and** exclude the plate (1, 8) |
| action starts too early | nothing else to do | incompatible occupying action (1) |
| subject tiny / one locked wide | `SCALE STATE`, or rule density | delete it; carry scale above and behind; write coverage (2, 9, 10) |
| unwanted object keeps appearing | named in a negative | describe the surface completely; delete the word (1, 2) |
| kill reads as a kiss | faces toward each other, limbs unassigned | from behind, named side, arms down, whole-frame test (7) |
| the money shot isn't shown | a "never shown" clause | grep discretion clauses (3) |
| white void mid-clip | near-white reference, or empty-background frame 0 | recrop; state the location persists through the effect (4, 8) |
| something glows that should be dark | "unlit" | positive equality (4) |
| camera moves when locked | stated once | three sections (11) |
| cuts drift late | cut times without durations | shot budget: absolute durations + ranking + overrun rule |
| fight feels hollow / turn-based | only attacker described; no cost | every body acts every shot; named persistent injuries; hero takes damage early (1, 5) |
| ground strike becomes a shockwave | weapon hits non-body | weapon never strikes water, stone or air (4) |
| identity drifts | prompt fragment | an approved turnaround riding as `<Subject N>` (8) |
| occlusion transition underdelivers | instruction too abstract | concrete simile, strongly positive ("the pendant fills the frame edge to edge like a gold coin held to the lens") — fixed 1 of 2, improved the other |

---

## Economics
On one 20-clip board, 12 re-rolls cost **60 % on top** of the board. Laws 2 and 3 alone would
have saved nine of the twelve. That is what `preflight.py` is for.

---

## Appendix A — Grounded combat / action (genre layer)

Use when the target is a photoreal fight. Structure: `subject_definitions` carries the locks
and **exactly ONE weapon** per character and who talks · `summary` states duration, body-to-body
hits with persistent damage, no shockwaves, combatant count, "all accounted for in the final
frame" · `retention_analysis` per subject: shots + `fully_preserved`, then **what is added**
(wounds, blood, mud, dented plate) · `detailed_description`: one look paragraph (light,
screen-direction lock, "never still", cost), then 7–8 timestamped shots for 15 s with lens and
move · soundscape in dynamics language (near silent between beats, hard transients) · score
cuts to nothing for the last two shots.

Shot pattern that held: low wide master → OTS on first attacker, hero **takes** damage → tight
low on hero, first kill, injury named → handheld on second attacker, roar, talker's line
off-screen → low tracking grab/slam → push to the leader, line cut off → MCU hero checks wound,
hoarse ≤3-word line, looks at the fallen not the lens → slow pull to wide, every body with its
injury, hero hunched, breathing, hold.

Dialogue: one talker among enemies, 2–3 lines; hero one roar (as action) and one line at the
end; always accent + class + mood + pace; number speakers by first vocal event. If it still
collapses to a master wide: split into 3 × ~5 s clips with the same `subject_definitions`.

Look block (paste-ready): *Photoreal cinematic dark fantasy shot like a live-action feature:
shallow depth of field on close shots, hard cold key from [source] cutting the [mist] so faces
and steel separate from background, deep charcoal shadows, warm [fire] rim. Screen direction
holds throughout: [A] always on the hero's left, [B] on his right, [C] rear-centre; eyelines
match across cuts. The hero is never still. Grounded adult violence with cost; wounds open,
bleed and stay. Every strike lands on a body — never water, stone or air.*

## Appendix B — Reels / get-ready-with-me format
See `templates/formats/reel.md`. Key findings: H3 does not reliably transform a garment
mid-generation — build state changes as independent clips cut at the most-occluded frame;
accessories/fabric pushed into the lens **are** the transitions; identity holds across 8–11
independent Ref2VA generations from sheets with no LoRA; a "smartphone camera" phrase reads as
a held prop — write *"as if filmed on a phone held stationary at waist height"*.
