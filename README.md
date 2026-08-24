# Movie Maker v2

Local-only short-film / episodic video pipeline. [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
(Krea-2 stills, Flux-2 Klein edits, MiniMax H3 motion + native audio) driven headless from Claude
Code, via the `comfy-draftsman` MCP for graph work and a local HTTP API for job queuing. No paid
services, ever — everything runs on local hardware.

This repo is **the build tool, not the creative work**. Productions (scripts, prompts, approved
references, job history) live in `productions/<slug>/` and are gitignored — they stay on the
render box in `F:\MovieMaker\`, mirroring `productions/`. What's tracked here is the shared layer:
tools, checks, templates, frozen graphs, and the rules that govern all of it.

## Read this first

- [`moviemaker-v2-SPEC.md`](moviemaker-v2-SPEC.md) — the contract. Founding rules, stage gates,
  file layout. Code and this file must agree; if they don't, one of them is wrong.
- [`LAWS.md`](LAWS.md) — model behaviour rules (read once per session by the agent).
- [`RUNBOOK.md`](RUNBOOK.md) — host-specific facts (paths, ComfyUI setup).
- [`routing.md`](routing.md) — which graph handles which job, and every settled lesson about
  getting H3/Krea-2/Klein to behave.

## The pipeline

A production moves through named gates, each a script with an exit code — no prose gates:

```
DEVELOP → BRIEF → CANON → AUDIO → BEATS → REFS → PROMPTS → PROOF → BOARD → CUT → POSTMORTEM
```

Approval at each gate means Ronan sets `status: approved` in the relevant file and commits.
Cheap before expensive: words → stills → one proof clip → the full board → the cut.

## Commands

| Command | What it does |
|---|---|
| `python tools/smoke.py` | every module imports (run at session start) |
| `python tools/drift.py <slug>` | production hasn't diverged from the shared layer |
| `python tools/new_production.py <slug> --format film\|show --title T [--unit 'S01E01 - N']` | the only way a production is created |
| `python tools/contract.py <slug>\|--all` | cross-file facts agree (beats, prompts, audio, refs) |
| `python tools/migrate.py` | bring productions up to the current `TEMPLATE_VERSION` |
| `python tools/preflight.py <slug> <unit\|.> <file.lines>` | refuse a prompt before it costs a render |
| `python tools/render.py <slug> <unit\|.> <job_id> [--dry-run\|--proof\|--requeue]` | queue a `jobs.jsonl` row |
| `python tools/landed.py <slug> [--watch]` | copy finished renders out, ffprobe, filmstrip, `renders.jsonl` |
| `python tools/refqc.py <png> --kind sheet\|crop\|plate [--figures N] [--record slug]` | measure a reference candidate (REFS gate) |
| `python tools/clipqc.py <clip.mp4> [--ref plate.png] [--frames N]` | measure a landed clip |
| `python tools/assemble.py <slug> <unit\|.> <cut>` → `cutqc.py <cut.json>` → `tag.py <cut.json>` | build the cut, verify it, produce review copies |
| `python tools/<check>.py --selftest` | calibrate a check against `calibration/` |

## Founding rules (full list: spec §0)

1. A check that does not measure the delivered artifact is not a check. No prose gates.
2. Cheap before expensive — a gate before every stage that costs real render time.
3. One fact, one file, cross-checked — `contract.py` refuses when two files disagree.
4. Nothing is typed twice; durations derive from measured audio or the H3 frame grid.
5. Refuse, don't warn, when the invariant is structural. No `except: pass`.
6. Never delete a render — reject by renaming `*__rej_<reason>.*`.
7. Identity is imported, never typed — one `identity.py` per production.
8. Productions own only `identity.py` + content. Everything else is shared above
   `productions/`; `drift.py` refuses any production that diverges.

## Graphs

Four frozen ComfyUI graphs live in `workflows/`, deployed via `workflows/deploy.py`:

- `mm_image_v1` — Krea-2 stills (sheets, plates, look tests).
- `mm_clip_v1` — MiniMax H3 reference-conditioned clips, up to 9 ref images / 3 ref audios,
  fixed 1536×864 (16:9).
- `mm_chain_v1` — MiniMax H3 long-form / lip-sync chain, fixed 1536×864 (16:9), context-loop with
  checkpointing, for anything needing a real vocal track driving lip-sync.
- `mm_ifl_v1` — first/last-frame pinned clips for the storyboard path (continuity by construction).

Graphs are edited only via the `comfy-draftsman` MCP and are never hand-saved from ComfyUI's own
UI; jobs are data (`jobs.jsonl`), never a saved graph variant.

## Working rules

- No LoRAs by default; one is added only as a proven speed-up or workflow improvement.
- `render.py` sets widgets and node modes only — never adds, removes, or rewires a node.
- Media (renders, refs, audio) lives at `F:\MovieMaker\`, mirroring `productions/`, and never
  enters git except approved `*_APPROVED_*.png` reference stills.
