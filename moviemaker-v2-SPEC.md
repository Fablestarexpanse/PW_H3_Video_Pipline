# Movie Maker v2 — Design Spec

Local-only short-film and episodic video pipeline. ComfyUI (Krea-2 stills, Flux-2 Klein edits,
MiniMax H3 motion + native audio) driven headless from Claude Code on Ronan's box. The pipeline is
**its own git repo and its own Obsidian vault**, separate from the Feyndral vault. No paid
services, ever.

This spec is the contract the code is built against. Where the code and this file disagree, fix
one of them the same session.

---

## 0. Founding rules

1. **A check that does not measure the delivered artifact is not a check.** Every gate is a
   script with an exit code. Prose gates do not exist.
2. **Cheap before expensive.** Words → stills → one proof clip → the board → the cut. A stage
   does not start until the previous stage's artifact carries `status: approved` in a file.
3. **One fact, one file, cross-checked.** Anything that must be true in two places is written
   once and imported. `contract.py` refuses when two files disagree.
4. **Nothing is typed twice.** Every duration derives from measured audio or the H3 frame grid.
   Quantise on the running total, never per beat.
5. **Default to the cheapest path that ships.** Turnaround sheets → independent Ref2VA clips →
   hard cuts. LoRA, plates, FL2VA chaining and `tnew` are upgrades bought only when a named
   deliverable needs them.
6. **Refuse, don't warn**, when the invariant is structural. Never `except: pass`. Every check
   prints what it measured, not only its verdict, and says how decisive the result was.
7. **Metrics rank suspicion; the picture decides.** Every clip gets a filmstrip on landing.
   Every metric is calibrated against known-good and known-bad clips kept in the repo, and its
   known failures are published beside it.
8. **A lesson is a check, or it didn't happen.** A finding observed twice becomes a refusal, a
   template fix, or is deleted. The log holds *why*, never *what* — git holds what.
9. **Never delete a render.** Reject by renaming `*__rej_<reason>.*`; every selector skips it.
10. **Identity is imported, never typed.** Cast, references, seeds, stacks and voice locks live in
    one `identity.py` per production, hard-failing while blank.
11. **Productions cannot drift from the system.** A production owns only the fields `identity.py`
    declares; everything else — tools, checks, templates, laws, workflows — is shared and lives
    above `productions/`. A lesson learned on one production lands in the shared layer the same
    session, so every other production has it the next time it runs. `drift.py` refuses any
    production whose structure, template version or tool usage diverges from the shared layer.

---

## 1. Stages and gates

```
DEVELOP → BRIEF → CANON → AUDIO → BEATS → REFS → PROMPTS → PROOF → BOARD → CUT → POSTMORTEM
   ▲G0       ▲G1     ▲G2            ▲G3      ▲G4     (preflight)  ▲G5     (qc)   ▲G6
```

| Stage | Artifact | Gate | Approve before | Gate script refuses when |
|---|---|---|---|---|
| DEVELOP | `development.md` + look-test contact sheet | G0 | writing the brief | — (creative; ends in "yes" or "no") |
| BRIEF | `brief.md` — one page, five decisions (runtime, aspect, audio source, cast count, one-off vs format) | G1 | any canon | any of the five decisions blank |
| CANON | `characters/*.md`, `locations/*.md` (spec in prompt words; ≤2 adjectives per axis) | G2 | any pixel | a recurring character lacks a spec; a spec has 3+ adjectives on one axis |
| AUDIO | `audio/` measured: duration, sample rate, stems | — | beats | track declared but not measured; stem duration ≠ master |
| BEATS | `beats.csv` — beat · frames (grid) · mode · refs · state changes · cut time | G3 | any render | frames not on 17k+5; refs not in identity; setup unpaid (consistency read); runtime ≠ measured audio |
| REFS | one sheet per character/prop, one empty template per location, optional master frame; `renders.jsonl` rows | G4 | any clip | any `<Picture N>` not `approved`; % pixels >235 ≥ 1.5 %; seed not frozen; prompt not stored verbatim |
| PROMPTS | `prompts/<unit>.lines` | preflight | queueing | see §3 preflight |
| PROOF | one clip, the hardest beat; `costs.csv` row | G5 | the board | no measured cost row at the shipped length; identity not confirmed by Ronan |
| BOARD | clips + `renders.jsonl` + filmstrips | clipqc | assembly | any clip fails clipqc |
| CUT | master + tagged + web copy | cutqc | delivery | frame sum ≠ beats; blown/black frames; codec mismatch; boundary drift |
| POSTMORTEM | `postmortem.md` + findings promoted | G6 | next production | a finding with count ≥ 2 has no check, fix, or deletion |

Approval is Ronan changing `status:` and committing. A proof clip on unapproved refs is permitted
once per production; a board is not.

---

## 2. Single source of truth per production — `identity.py`

```python
TITLE = ""                 # refused while blank
FORMAT = "film" | "show"
ASPECT = (w, h)            # clips are sized from the master ref via GetImageSize, never typed
STYLE_STACK = [...]        # locked at kickoff; NegPip is the only edit point
CAST = {"wren": {"sheet": "refs/wren_APPROVED_811003.png", "seed": 811003, "slot": 2}}
LOCATIONS = {...}
VOICES = {"wren": "<byte-identical (S1) identity phrase>"}   # pasted by code, never by hand
AUDIO = {"master": "...", "stem": "...", "duration": 167.92}  # measured, not typed
WORKFLOWS = {"image": "...", "edit": "...", "clip": "...", "chain": "..."}
```

Everything imports it. `contract.py` asserts: every ref in `beats.csv` exists in `CAST`/
`LOCATIONS`; every voice used in prompts exists in `VOICES`; every `<Picture N>` slot in the
line file matches `slot`; `AUDIO.duration` equals the measured file; `slot_names.txt` count
equals beat count.

---

## 3. The checks

Each is a script in `tools/`, each exits 1 on failure, prints measurements, and has a
`--selftest` run against `calibration/` fixtures where applicable.

| Script | Runs at | Measures on | Refuses when |
|---|---|---|---|
| `smoke.py` | session start | every module imports in a subprocess | any import fails |
| `contract.py` | G3, G4, preflight, build | cross-file facts (§2) | any disagreement |
| `residue.py` | new production | beat ids / names from other productions | any found |
| `refqc.py` | G4 | mean luminance, % >235, % <20, medium, figure count via gap scan | % >235 ≥ 1.5; figure count ≠ requested; luminance outside the block it feeds |
| `preflight.py` | before every queue | the exact prompt line | discretion clause (`never shown`, `out of view`, `hidden`, `not visible`, `off-screen`, `implied`, `we do not see`); stale negative; `SCALE STATE`; frame zero not described in `retention_analysis`; block count > template; unapproved ref; unescape round-trip not byte-exact; seed on randomize; duration widget off the 0.1 step; frames not on grid |
| `canvas.py` | before queue | latent token budget | over budget (thrash, not failure) |
| `render.py` | every queue | the job row + graph | graph not in `routing.md`; any ref not `APPROVED` (except the one permitted proof clip); would require a node add/remove/rewire |
| `landed.py` | on every completion | `save_output` → copy out → `ffprobe` → filmstrip (6 frames) → `renders.jsonl` row | frame count ≠ expected |
| `clipqc.py` | after landing, before cut | frames; ref-leak corr first 4 s; blown; black; cuts (strobe-pair filtered); **local block stats** (peak/median block motion, largest jump/median, edge-energy growth); grade | corr > 0.50; blown/black; cuts on a one-shot clip; local anomaly above calibrated threshold |
| `assemble.py` | cut | frame-exact segments, stream-copy concat, named `SRC` per slot, full rebuild | any source missing or `__rej_` |
| `cutqc.py` | on the delivered file | frame sum vs beats; codec/geometry/rate/pixfmt across segments; blown/black; boundary drift; audio length vs picture (2 ms) | any mismatch — never loosen the tolerance |
| `tag.py` | cut | slot-tagged review copy + 720p web copy | — |
| `costs.py` | G5 | `costs.csv` row for the shipped length/regime | no row → GATE D cannot be quoted |
| `findings.py` | postmortem | `findings.jsonl` counts | count ≥ 2 with no `check:` / `fix:` / `dropped:` |

**Calibration rule:** `clipqc.py --selftest` must separate `calibration/bad/*` from
`calibration/good/*`. If it does not, the metric is removed, not tuned.

---

## 4. Laws that the prompts obey (already measured — do not relearn)

Kept verbatim in `LAWS.md`. Summary the preflight encodes:

- The model builds from presence, not absence. To remove a thing, describe what occupies the
  space, by equality with something already in frame.
- Vivid description beats attached negation. Escalation: delete the fighting word → declare a
  winner → delete the competing block → change the shot.
- "Not shown" is obeyed about the shot you want. Grep for it.
- Frame zero must be described positively or the reference plate is reproduced (+0.97 → +0.03).
- A reference teaches everything in it. State what is and is not taken from each `<Picture N>`.
- Continuity is a timed STATE with an anti-tidying clause, in `retention_analysis`.
- Scale rides above and behind the subject, never in camera distance. No `SCALE STATE`.
- Rule density itself collapses a clip to one locked wide. Cut a rule before adding one.
- The important thing is stated three times in three sections; once in one paragraph is padding.
- Krea-2: prompt negatives do nothing at cfg 1.0; NegPip weights −1.2…−1.5 work for standing
  style-stack taxes only; one-off fixes are Klein edits, never rerolls. Width beats "three".
- H3 grid is 17k+5 at 24 fps; widget is seconds at 0.1 step; `13.0` → 328 frames. Cost is
  superlinear; measure at the shipped length. Trim handles ~1.0 s head / ≥0.8 s tail.

---

## 5. Where files live

Two trees, one hard line: **text and approved refs in the repo; everything heavy on the drive.**

### 5a. The repo — `C:\Users\Brian\Documents\MovieMaker` (git + Obsidian vault)

```
MovieMaker/
  CLAUDE.md              ≤40 lines: what this is, the stages, the commands, founding rules 1–3, 11
  STATUS.md              GENERATED by /start from status: fields — never hand-edited
  LAWS.md                model behaviour (prose; the one long file read every session)
  RUNBOOK.md             comfy-draftsman and host facts; what only Ronan does by hand
  routing.md             job → workflow → settings, one table
  costs.csv              frames, res, regime, refs, minutes, date, production
  findings.jsonl         {finding, count, productions[], status, check|fix|dropped}
  .claude/commands/      start develop new-production canon beats refs preflight proof board cut postmortem
  .claude/skills/        h3-prompt-writing · reference-sheets · assembly
  .git/hooks/            post-session commit; pre-commit runs smoke + drift
  tools/                 §3 scripts — THE ONLY place logic lives
  workflows/             clean base JSONs: image · edit · clip · chain. Source of truth; deployed
                         copies in ComfyUI are overwritten from here, never edited in place
  templates/
    production/          the whole production skeleton (copied by new-production, never rendered)
    TEMPLATE_VERSION     integer; bumped on any change to templates/ or tools/ contracts
  calibration/           manifest.json of good/bad clips (media on drive) for clipqc --selftest
  worlds/<World>/        canon shared across productions + approved recurring refs + manifest
  productions/<slug>/    see 5c
```

### 5b. The drive — `F:\MovieMaker\` (media, never in git)

```
F:\MovieMaker\
  calibration\good\  calibration\bad\
  <slug>\
    refs\candidates\          every seed ever rendered; rejects renamed *__rej_<reason>.png
    <unit>\clips\              copied out of ComfyUI the moment each lands
    <unit>\filmstrips\
    <unit>\cuts\               master · tagged · web
```

Mirrors the repo's production structure exactly, so a path is derivable from either side.
`tools/paths.py` owns the root as `MOVIEMAKER_MEDIA` — the only file with a drive letter in it.

ComfyUI's own `input/` and `output/` are scratch: refs are copied in when a clip needs them,
renders are copied out by `landed.py` immediately, and neither is ever the only copy of anything.
ComfyUI's saved workflows are deployed from `workflows/`, not the reverse.

### 5c. One production — created only by `/new-production`, never by hand

```
productions/<slug>/
  identity.py            the ONLY file a production may customise (fields in §2)
  template_version       written at creation; drift.py refuses if < TEMPLATE_VERSION
  brief.md  development.md
  characters/  locations/
  refs/                  *_APPROVED_*.png (committed) + manifest.json (every seed, hash, F: path, refqc)
  renders.jsonl
  <unit>/                film: the production folder itself · show: S01E01 - <name>/
    beats.csv  slot_names.txt  prompts/<unit>.lines  postmortem.md
```

A production folder contains **no code and no rules**. If a production needs a behaviour the
system lacks, the behaviour is added to `tools/` or `templates/` with a `TEMPLATE_VERSION` bump
and every existing production is migrated by `tools/migrate.py` in the same commit.

### 5d. Anti-drift — `tools/drift.py` (runs in the pre-commit hook and at `/start`)

Refuses when any production has:
- a file not in the template skeleton, or a required file missing;
- `template_version` older than `TEMPLATE_VERSION` (run `migrate.py`);
- a `.py` other than `identity.py`, or an `identity.py` field the template does not declare;
- a prompt line whose `<Picture N>` slot map differs from `identity.CAST[*].slot`;
- a workflow name not in `routing.md`, or a ComfyUI-side workflow whose hash differs from `workflows/`;
- a finding in `findings.jsonl` at `count ≥ 2` still `open`.

Learning flows one way: production → `findings.jsonl` → shared tool/template/law → all
productions. A post-mortem that leaves a lesson inside its own folder fails G6.

## 6. Build order

1. `season_paths`-style `paths.py`: ffmpeg, ffprobe, ComfyUI root, input/output dirs, from env
   with defaults; prints what resolves.
2. `workflows/` — the four frozen graphs from §7a, built clean, exported and committed, plus
   `deploy.py`. Move every existing ComfyUI workflow into an archive folder on the instance.
   This alone removes the surgery done on every clip today.
3. `templates/production/` + `TEMPLATE_VERSION` + `new_production.py` + `identity.py` template
   + `contract.py` + `smoke.py` + `residue.py` + `drift.py` + `migrate.py` + the pre-commit hook.
4. `preflight.py` with `--selftest` against a fixture set of known-bad prompts.
5. `render.py` + `jobs.jsonl` (§7b), then `landed.py` + `renders.jsonl` + filmstrip.
6. `refqc.py` (G4 finally measurable).
7. `clipqc.py` rewrite with local block stats + calibration set.
8. `assemble.py` + `cutqc.py` + `tag.py`.
9. `/develop`, `/brief`, `/beats`, `/refs`, `/proof`, `/board`, `/cut`, `/postmortem` commands.
10. Migrate one existing production (Wren — most complete) as the first real run; its faults
    become the first `findings.jsonl` entries. `worlds/` is populated by copying (not linking)
    the Fablestar/Perpetua canon out of the Feyndral vault; the Feyndral vault is left untouched.

Not yet: LoRA training path, FL2VA chaining, `tnew`, multi-speaker locks. Each is a named
upgrade with its own proof clip when a production needs it.

---

## 7. Workflows: graphs are frozen, jobs are data

The old system grew 33+ saved workflows because every job (a clip, a sheet, a trailer) was saved
as a new graph. In v2 **a saved workflow is a graph only** — nodes and links — and **everything
that varies per job is data** that `tools/render.py` applies at submit time. Nothing is ever
saved back to ComfyUI from a run.

### 7a. Exactly four graphs, in the repo, deployed to ComfyUI

| Graph | Job | Variable inputs (and nothing else) |
|---|---|---|
| `mm_image_v<n>.json` | sheets, templates, plates, look tests | prompt line index · NegPip line · inline LoRA string · seed · size · `filename_prefix` |
| `mm_edit_v<n>.json` | Klein edit of an existing render | source image · edit prompt · seed · `filename_prefix` |
| `mm_clip_v<n>.json` | any single H3 generation | prompt line index · up to 9 `ref_image` filenames · up to 3 `ref_audio` · duration widget · seed · `filename_prefix` · master-ref filename (size via `GetImageSize`) |
| `mm_chain_v<n>.json` | `tnew` long-form / lip-sync | plan JSON · run_name · fingerprint · ref filenames · source + mux audio · base_seed |

Each ships clean: **zero** demo content, every `ref_image` slot present but pointing at a
committed 64×64 neutral grey `null_ref.png`, prompt read from a line file via
`CUN_TextFileLineLoader → JWStringUnescape`, seed fixed (not randomize), size from the master
ref, `SaveVideo`/`SaveImage` prefix as a widget. `workflows/deploy.py` copies them into
ComfyUI's workflow folder and `drift.py` refuses if the deployed hash differs from the repo.

A change to a graph is a change to the JSON **in the repo**, with a version bump and a line in
`routing.md`. The old copy is kept under `workflows/archive/`. That is the only way a new
workflow ever comes to exist.

### 7b. A job is a row, not a file

`productions/<slug>/<unit>/jobs.jsonl` — one row per thing queued:

```json
{"id":"dm_b03_s850003","graph":"mm_clip_v1","line":3,"refs":{"0":"wren_masterwide_APPROVED_820005.png","1":"wren_turnaround_APPROVED_811003.png"},
 "audio":{},"duration":5.0,"frames":124,"seed":850003,"prefix":"MovieMaker/wren/S01E01/clips/b03","status":"queued","prompt_id":"…"}
```

`render.py <job_id>`:
1. `import_workflow` the graph fresh from the repo copy (never from a prior session id — ids
   die on reconnect, so nothing depends on one).
2. Set widgets from the row. Unused `ref_image`/`ref_audio` slots are set to **bypass** — a
   node-mode change is part of the submitted API prompt, not a graph edit, and it is what keeps
   unused refs out of the conditioning without rewiring anything.
3. `validate_workflow`; run `preflight.py` on the resolved line; refuse on either.
4. `run_workflow(wait=False, roll_seeds=False, front=False)`; write `prompt_id` to the row.
5. Never `save_workflow`. The repo JSON is the saved state; the row is the job.

`landed.py` polls rows with `status: queued`, copies outputs out, verifies frames, writes the
filmstrip and the `renders.jsonl` row. A restart that clears ComfyUI's history loses nothing —
every row still has its parameters, so re-queueing is `render.py --requeue`.

### 7c. Consequences

- **R-010 (save before run) is retired.** There is nothing to save.
- **R-028 becomes enforceable**: `render.py` can only set widgets and node modes; it has no
  code path that adds, removes or rewires a node.
- Reproducing any render ever made is `render.py <job_id>` — the row, the graph version and
  the ref hashes pin it. The MP4's embedded prompt (`ffprobe format_tags=prompt`) is the
  backup, not the source.
- The existing 33 workflows are moved to `workflows/archive/` on the ComfyUI side (not deleted)
  and are not in `routing.md`. `drift.py` flags any production referencing one.
- Per-production variation lives in `identity.py` (`STYLE_STACK`, `CAST[*].slot`, `WORKFLOWS`
  pinned to graph versions) — never in a per-production graph.
