# Movie Maker v2

Local-only short-film / episodic video pipeline: ComfyUI (Krea-2 stills, Flux-2 Klein edits,
MiniMax H3 motion + audio) driven headless via the `comfy-draftsman` MCP. Contract: `moviemaker-v2-SPEC.md`.
Model behaviour: `LAWS.md` (read once per session). Host facts: `RUNBOOK.md`. Job routing: `routing.md`.
Prompt shape: `templates/clip_prompt_template.md`; reels: `templates/formats/reel.md`; skills: `.claude/skills/`.

## Stages
DEVELOP → BRIEF → CANON → AUDIO → BEATS → REFS → PROMPTS → PROOF → BOARD → CUT → POSTMORTEM
Each gate is a script in `tools/` with an exit code. Approval = Ronan sets `status: approved` and commits.

## Commands
- `python tools/paths.py` — resolve host paths; creates `F:\MovieMaker` skeleton
- `python tools/smoke.py` — every module imports (session start)
- `python tools/drift.py` — no production diverges from the shared layer (pre-commit)
- `python tools/new_production.py <slug> --format film|show --title T [--unit 'S01E01 - N']` — the only way a production is created
- `python tools/contract.py <slug>|--all` — cross-file facts agree (G3/G4/preflight/build)
- `python tools/migrate.py` — bring productions to `TEMPLATE_VERSION` after a template/tool change
- `python tools/preflight.py <slug> <unit|.> <file.lines>` — refuse a prompt before it costs a render (LAWS)
- `python tools/render.py <slug> <unit|.> <job_id> [--dry-run|--proof|--requeue]` — queue a jobs.jsonl row
- `python tools/landed.py <slug> [--watch]` — copy finished renders out, ffprobe, filmstrip, renders.jsonl
- `python tools/refqc.py <png> --kind sheet|crop|plate [--figures N] [--block LO HI] [--record slug]` — G4 measurement
- `python tools/clipqc.py <clip.mp4> [--ref plate.png] [--frames N] [--one-shot]` — post-landing QC
- `python tools/assemble.py <slug> <unit|.> <cut> [--head 24]` → `cutqc.py <cut.json>` → `tag.py <cut.json>` — the cut, its QC, its review copies
- `python tools/<check>.py --selftest` — calibrate a check against `calibration/`

## Founding rules (full list: spec §0)
1. A check that does not measure the delivered artifact is not a check. No prose gates.
2. Cheap before expensive: words → stills → one proof clip → board → cut. Gate before each.
3. One fact, one file, cross-checked — `contract.py` refuses when two files disagree.
11. Productions own only `identity.py` + content. Tools, checks, templates, laws are shared above
    `productions/`. `drift.py` refuses any production that diverges.

## Working rules
- Graphs are frozen (`workflows/`, four of them); jobs are data (`jobs.jsonl`). Never `save_workflow`.
- Graphs are built/edited/inspected only via the `comfy-draftsman` MCP; jobs are queued only via `render.py` (local HTTP API).
- `render.py` sets widgets and node modes only — never adds, removes or rewires a node.
- Refuse, don't warn. No `except: pass`. Print what was measured.
- Never delete a render: rename `*__rej_<reason>.*`.
- New finding the spec didn't predict → `findings.jsonl` with `count: 1`.
- Media lives at `F:\MovieMaker\` (mirrors `productions/`), never in git. `tools/paths.py` owns the root.
