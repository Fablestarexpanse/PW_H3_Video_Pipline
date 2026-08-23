# Paste this into Claude Code, in an empty folder, with `moviemaker-v2-SPEC.md` beside it

---

You are building **Movie Maker v2**, a local-only generative video pipeline, from the spec in
`moviemaker-v2-SPEC.md`. Read it fully before writing anything. It is the contract; if you find
it contradicts itself, stop and ask rather than pick a side silently.

**Also beside it is `port/`** — the old system's paid-for knowledge already edited into v2
shape: `LAWS.md`, `RUNBOOK.md`, `routing.md`, `costs.csv`, `findings.jsonl`, the
`reference-sheets` and `assembly` skills, `templates/` (production skeleton, clip prompt
template, reel format) and `MIGRATION.md`. Copy `port/` into the repo root as step 0. These
files are inputs to the build, not outputs of it: the checks in §3 of the spec must enforce
what they say (e.g. `preflight.py` enforces the checks named in `LAWS.md`).

**Context you need:**

- Host: Windows, RTX 4090, ComfyUI at `F:\Stability Matrix\Packages\ComfyUI`. ffmpeg/ffprobe on
  PATH. Python 3.10+. The `comfy-draftsman` MCP server is the only way ComfyUI is driven — never
  hand-build a graph; load a saved workflow and set widget values only.
- Models: Krea-2 (stills, cfg 1.0, 8–11 steps, 1344×768), Flux-2 Klein 9B distilled (image
  edits), MiniMax H3 local weights (motion + native audio, 24 fps, 17k+5 frame grid). Nothing
  paid, no `api_*` templates, no `partner/` nodes, ever.
- The `h3-prompt-writing` skill is the structural authority for H3 prompts. Copy it into
  `.claude/skills/` unchanged.
- This repo lives at `C:\Users\Brian\Documents\MovieMaker` and is its own Obsidian vault. Media
  lives at `F:\MovieMaker\` and never enters git. The old Obsidian vault
  (`C:\Users\Brian\Documents\Feyndral\Movie Maker`) holds two weeks of measured findings; read
  from it, never write to it. `LAWS.md` in the spec summarises them; the full `Prompting Laws.md`,
  `Model Routing.md`, `Workflow Registry.md` and `Assembly Guide.md` there are source material.
  Read them for the numbers; do not copy their structure.

**Working rules for this build:**

1. Follow the **build order in §6 of the spec**, one step per commit, and stop after each step to
   show me what it does with a real run (a smoke test, a selftest, a dry run) before moving on.
2. Every script in `tools/` exits 1 on failure, prints what it measured, and has `--selftest`
   where a fixture can exist. No `except: pass`. No warnings where the spec says refuse.
3. `CLAUDE.md` stays under 40 lines. If you want to put more in it, it goes in a file CLAUDE.md
   points at.
4. Write `RUNBOOK.md` as you discover tool facts, not at the end.
5. Do not touch ComfyUI until step 2 (building the four frozen graphs from spec §7). Graphs are
   frozen; jobs are data (`jobs.jsonl` + `render.py`). No code you write may call
   `save_workflow` after a run, and `render.py` must have no code path that adds, removes or
   rewires a node — widgets and node modes only. When you do, inspect
   the live node schemas with `get_node_info` before documenting any widget or JSON format.
6. Every finding you hit that the spec didn't predict goes into `findings.jsonl` with `count: 1`.
7. Commit at the end of every step with a message that says what now refuses that didn't before.
8. **Nothing production-specific goes anywhere except that production's `identity.py` and its
   content files.** Every behaviour, check, rule and template is shared. If a production needs
   something the system lacks, add it to `tools/` or `templates/`, bump `TEMPLATE_VERSION`, and
   migrate every production in the same commit. `drift.py` is the enforcement — build it in
   step 3 and keep it in the pre-commit hook from then on.

**Start now with step 1:** `tools/paths.py` — resolve ffmpeg, ffprobe, ComfyUI root, its input
and output directories, and `MOVIEMAKER_MEDIA` (default `F:\MovieMaker`) from environment
variables with defaults for this machine; print what resolves and what is missing; exit 1 if
anything required is absent; create the `F:\MovieMaker\` skeleton from §5b if it doesn't exist.
Then the repo skeleton from §5a with empty placeholders and a `.gitignore` that excludes all
media except `refs/*_APPROVED_*.png`.
Initialise git and make the first commit. Show me the output of `python tools/paths.py`.

---

# Optional second prompt, after step 10 lands

Migrate `Productions/Wren` from the Obsidian vault into `productions/wren/`. Fill `identity.py`
from the Bible (cast, approved refs, seeds, no LoRA, the before-state sheet). Convert its eight
Dark Muse beat prompts into `prompts/dark_muse.lines`, run `preflight.py` on them, and report
every refusal it raises against prompts that already rendered clean — those are either false
positives to calibrate out, or real faults that shipped. Do not render anything.
