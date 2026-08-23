---
status: draft
---
# Wren / S01E01 - Dark Muse — Post-mortem (migrated 2026-08-23; rendered 2026-08-17/18 on the old system)

## What shipped
11 beats · 1466 frames · 61.08 s · 768×1344 · zero re-rolls. `Wren_DarkMuse_v1.mp4` delivered from a concat-filter
re-encode (not stream-copied). Minutes not measured (Bible: "not separately re-measured") — no `costs.csv` row; G5 could
not have been quoted under v2.

## What the v2 gates say about prompts and clips that "rendered clean"

Every Dark Muse line and clip was run through the v2 checks as migrated. Each refusal is either a false positive to
calibrate out (→ a check changed) or a real fault that shipped (→ stays refused until fixed).

| Check | Beats | Verdict | What changed |
|---|---|---|---|
| preflight `unapproved <Picture 1>` | 1–11 | **real** — the Dark Muse master wide `870002` (beats 2–11) and the before-state `811003` as slot 0 (beat 1) rode on a GATE B2 waiver; `870002` is a manifest candidate, not approved | nothing — approve `870002` (→ `refs/darkmuse_master_APPROVED_870002.png`, `identity.LOCATIONS`) or it stays refused |
| preflight `frame_zero` | 1, 2, 4, 7 | **real on beat 1**: no frame-zero description and the Bible records "beat 1's opening frame reads as a noticeably fuller body … self-correcting by mid-frame" — LAWS §1 filling the vacuum from the older `811003` reference. **Evidence on 2, 4, 7**: frame zero described in `detailed_description [Shot 1]` only, leak ≤ +0.37, fine — one data point that the rule is stricter than needed when slot 0 is a character/master ref rather than an empty plate | law unchanged on one data point; finding logged |
| preflight `frame_zero` | 3, 5, 6, 8–11 | **false positive** — these beats are master-locked by design (the reel format): frame zero IS `<Picture 1>` | `beats.csv mode = ref2va-master`; preflight accepts `<Picture 1>` named in `retention_analysis` |
| clipqc `ref_leak` +0.999 @ frame 0 | 5, 6, 9, 10, 11 (and +0.62…+0.88 mid-clip on 3, 7, 8) | **false positive as a fault; true as a measurement** — the master wide is reproduced verbatim at frame 0, exactly LAWS §1's mechanism, here intended | `clipqc --expect-master` (from `mode`) inverts the check: refuses if the clip does NOT open on the master |
| clipqc `--expect-master` | 2, 4, 7 | **correct refusal** — seated stool shot, detail insert, ECU: not master-framed, by design | those beats are `mode = ref2va` |
| clipqc `black` 122–123 + `cut` 116 | 2 | **false positive** — the scripted full-frame occlusion to black that the Bible records as the one that worked | `state_changes = occlusion-tail:12` → `clipqc --occlusion-tail 12` |
| clipqc local p/m 78 (advisory) | 1 | consistent with the body-shape anomaly at the open | advisory only |
| contract `ref darkmuse_master not in identity` | 2–11 | **real** — same as the first row: G3/G4 cannot hold until `870002` is approved | — |
| refqc sheet figure count | `811003` reads 1 | known failure of the gap scan on a 768-wide portrait sheet (loose hair spans the gaps); `810003` counts 3/3 | documented in `refqc.py`; counted by eye |
| refqc plate `> 235` 8.0 % | sunroom `820102` | the backlit curtain, by design; the 1.5 % rule was measured on a crop | Ronan to rule for plates |

## What the measurements said
Beat 2 occlusion: last frame solid black (lum < 8) — delivered. Beat 5 occlusion: no black tail (grade min 39) — the
Bible's "improved but did not fully match", now a number. Ref correlation to the master wide at frame 0: 5/6/9/10/11 =
+0.999; 3 = +0.88@95; 8 = +0.62@43; 7 = +0.76@95; 2/4 ≤ +0.37.

## What outlives this production
- `beats.csv mode ref2va-master` and `state_changes occlusion-tail:N` — format facts the checks now read (shared layer).
- Frame zero undescribed + an older reference = the opening-frame body anomaly (beat 1). A law, confirmed.
- The reel format itself → `templates/formats/reel.md` (still to port from the Bible's Format section).
